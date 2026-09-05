from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.scans.dao.scan_dao import ScanDAO as scan_dao
from app.scans.worker import run_discovery_scan
from app.domains.service.domain_services import DomainService as domain_service


class ScanService:
    """
    Handle the business logic for scan management
    """
    @staticmethod
    async def trigger_scan(db: Session, domain_id, triggered_by, background_tasks: BackgroundTasks):
        await domain_service.get_domain(db, domain_id)  # 404s if the domain doesn't exist
        scan = await scan_dao.create_scan(db, domain_id, triggered_by)
        background_tasks.add_task(run_discovery_scan, str(domain_id), str(scan.id))
        return scan

    @staticmethod
    async def get_scan_history(db: Session, domain_id, page: int, limit: int):
        await domain_service.get_domain(db, domain_id)  # 404s if the domain doesn't exist
        return await scan_dao.get_scan_history(db, domain_id, page, limit)
