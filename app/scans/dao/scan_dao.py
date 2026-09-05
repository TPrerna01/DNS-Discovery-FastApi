from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette import status
from fastapi import HTTPException

from app.scans.models import Scan, ScanStatus
from app.core.constants import SCAN_ALREADY_RUNNING


class ScanDAO:
    """
    Handle the scan lifecycle data access
    """
    @staticmethod
    async def create_scan(db: Session, domain_id, triggered_by=None) -> Scan:
        running_query = select(Scan).filter(Scan.domain_id == domain_id, Scan.status == ScanStatus.RUNNING)
        result = await db.execute(running_query)
        if result.scalars().first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": SCAN_ALREADY_RUNNING})

        scan = Scan(domain_id=domain_id, triggered_by=triggered_by, status=ScanStatus.PENDING)
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        return scan

    @staticmethod
    async def get_scan_history(db: Session, domain_id, page: int, limit: int):
        scan_query = select(Scan).filter(Scan.domain_id == domain_id)

        total_query = select(func.count()).select_from(scan_query.subquery())
        total = (await db.execute(total_query)).scalar()

        scan_query = scan_query.order_by(Scan.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await db.execute(scan_query)
        scans = result.scalars().all()
        return scans, total

    @staticmethod
    async def mark_running(db: Session, scan_id) -> Scan:
        scan = await db.get(Scan, scan_id)
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now()
        await db.commit()
        return scan

    @staticmethod
    async def mark_completed(db: Session, scan_id) -> None:
        scan = await db.get(Scan, scan_id)
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now()
        await db.commit()

    @staticmethod
    async def mark_failed(db: Session, scan_id, error_message: str) -> None:
        scan = await db.get(Scan, scan_id)
        scan.status = ScanStatus.FAILED
        scan.error_message = error_message
        scan.completed_at = datetime.now()
        await db.commit()
