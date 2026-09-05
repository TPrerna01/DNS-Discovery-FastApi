import uuid
from unittest.mock import patch

from sqlalchemy import delete, select

from conftest import TestSessionLocal, next_test_domain
from app.domains.models import Domain, DomainStatus
from app.scans.models import Scan, ScanStatus
from app.assets.models import Asset
from app.scans.worker import run_discovery_scan

# run_discovery_scan normally opens its own session via db_connection.SessionLocal (the
# app's real, pooled engine) - patched here to the NullPool-based TestSessionLocal for
# the same cross-event-loop reason conftest.py's run_db() exists. See conftest.py.
worker_session_patch = patch("app.scans.worker.SessionLocal", TestSessionLocal)


async def _seed_domain_and_scan():
    domain_id = uuid.uuid4()
    scan_id = uuid.uuid4()
    async with TestSessionLocal() as db:
        db.add(Domain(id=domain_id, name=next_test_domain(), status=DomainStatus.PENDING))
        db.add(Scan(id=scan_id, domain_id=domain_id, status=ScanStatus.PENDING))
        await db.commit()
    return str(domain_id), str(scan_id)


async def _cleanup(domain_id):
    async with TestSessionLocal() as db:
        await db.execute(delete(Domain).where(Domain.id == domain_id))
        await db.commit()


async def test_run_discovery_scan_persists_assets_and_completes():
    domain_id, scan_id = await _seed_domain_and_scan()

    fake_records = {
        "A": ["93.184.216.34"],
        "AAAA": [],
        "NS": ["ns1.example.com", "ns2.example.com"],
        "MX": ["10 mail.example.com"],
    }

    async def fake_resolve(resolver, domain_name, record_type):
        return fake_records[record_type]

    with worker_session_patch, patch("app.scans.worker._resolve_record", side_effect=fake_resolve):
        await run_discovery_scan(domain_id, scan_id)

    async with TestSessionLocal() as db:
        scan = await db.get(Scan, scan_id)
        domain = await db.get(Domain, domain_id)
        assert scan.status == ScanStatus.COMPLETED
        assert domain.status == DomainStatus.COMPLETED
        assert scan.started_at is not None
        assert scan.completed_at is not None

        assets = (await db.execute(select(Asset).filter(Asset.scan_id == scan_id))).scalars().all()
        assert len(assets) == 4  # 1 A + 0 AAAA + 2 NS + 1 MX

    await _cleanup(domain_id)


async def test_run_discovery_scan_marks_failed_on_unexpected_error():
    domain_id, scan_id = await _seed_domain_and_scan()

    async def boom(resolver, domain_name, record_type):
        raise RuntimeError("resolver exploded")

    with worker_session_patch, patch("app.scans.worker._resolve_record", side_effect=boom):
        await run_discovery_scan(domain_id, scan_id)

    async with TestSessionLocal() as db:
        scan = await db.get(Scan, scan_id)
        domain = await db.get(Domain, domain_id)
        assert scan.status == ScanStatus.FAILED
        assert scan.error_message == "resolver exploded"
        assert domain.status == DomainStatus.FAILED

    await _cleanup(domain_id)
