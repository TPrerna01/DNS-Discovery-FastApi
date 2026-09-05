import logging
from datetime import datetime

import dns.asyncresolver
import dns.resolver
import dns.exception

from app.assets.models import Asset, AssetType
from app.domains.models import Domain, DomainStatus
from app.scans.models import Scan, ScanStatus
from db_connection import SessionLocal

logger = logging.getLogger("app.worker")

# per-record-type lookup timeout, so one unresponsive domain can't block the worker
RESOLVER_TIMEOUT_SECONDS = 5

RECORD_TYPES = ["A", "AAAA", "NS", "MX"]

# these just mean "this domain has no records of this type" - not a scan failure
NO_RECORDS_ERRORS = (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout)


async def _resolve_record(resolver: dns.asyncresolver.Resolver, domain_name: str, record_type: str) -> list[str]:
    try:
        answer = await resolver.resolve(domain_name, record_type)
    except NO_RECORDS_ERRORS:
        return []

    values = []
    for rdata in answer:
        if record_type in ("A", "AAAA"):
            values.append(rdata.address)
        elif record_type == "NS":
            values.append(str(rdata.target).rstrip("."))
        elif record_type == "MX":
            values.append(f"{rdata.preference} {str(rdata.exchange).rstrip('.')}")
    return values


async def run_discovery_scan(domain_id: str, scan_id: str) -> None:
    """
    Resolve A, AAAA, NS & MX records for a domain and persist them as Assets.
    Runs as a FastAPI BackgroundTask - owns its own DB session, and must never
    leave the scan stuck in RUNNING, so every failure path marks it FAILED.
    """
    async with SessionLocal() as db:
        try:
            domain = await db.get(Domain, domain_id)
            scan = await db.get(Scan, scan_id)

            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.now()
            domain.status = DomainStatus.RUNNING
            await db.commit()
            logger.info(f"Scan {scan_id} started for {domain.name}")

            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = RESOLVER_TIMEOUT_SECONDS
            resolver.lifetime = RESOLVER_TIMEOUT_SECONDS

            asset_count = 0
            for record_type in RECORD_TYPES:
                values = await _resolve_record(resolver, domain.name, record_type)
                for value in values:
                    db.add(Asset(scan_id=scan.id, domain_id=domain.id,
                                 type=AssetType(record_type), value=value))
                    asset_count += 1

            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.now()
            domain.status = DomainStatus.COMPLETED
            await db.commit()
            logger.info(f"Scan {scan_id} completed for {domain.name}, found {asset_count} assets")
        except Exception as e:
            logger.exception(f"Scan {scan_id} failed for domain_id={domain_id}")
            await db.rollback()
            scan = await db.get(Scan, scan_id)
            if not scan:
                return
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.now()
            domain = await db.get(Domain, domain_id)
            if domain:
                domain.status = DomainStatus.FAILED
            await db.commit()
