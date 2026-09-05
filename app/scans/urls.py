import logging

from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from app.scans.dto.scan_schemas import ScanTriggerResponseSchema, ScanListResponseSchema
from app.scans.service.scan_services import ScanService as scan_service
from app.users.models import UserRole
from app.core.constants import ERROR_WHILE_TRIGGERING_SCAN, ERROR_WHILE_FETCHING_SCAN_HISTORY
from db_connection import get_db

from app.core.utils.common_auth_utils import CommonAuthUtils as auth_utils

logger = logging.getLogger("app.scans")

scan_router = APIRouter(prefix="/domains")


@scan_router.post("/{domain_id}/scan", response_model=ScanTriggerResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(request: Request, domain_id: str, background_tasks: BackgroundTasks,
                       db: Session = Depends(get_db),
                       current_user = Depends(auth_utils.require_roles(UserRole.ADMIN, UserRole.ANALYST))):
    """
    Manually trigger a discovery scan for a domain. Admin & Analyst only.
    """
    try:
        scan = await scan_service.trigger_scan(db, domain_id, current_user.id, background_tasks)
        return {"scan_id": scan.id, "status": scan.status}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to trigger scan for domain {domain_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_TRIGGERING_SCAN})


@scan_router.get("/{domain_id}/scans", response_model=ScanListResponseSchema)
async def get_scan_history(request: Request, domain_id: str, db: Session = Depends(get_db),
                           page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                           current_user = Depends(auth_utils.get_current_active_user)):
    """
    Return the scan history for a domain.
    """
    try:
        scans, total = await scan_service.get_scan_history(db, domain_id, page, limit)
        items = [{"scan_id": s.id, "status": s.status, "started_at": s.started_at, "completed_at": s.completed_at}
                for s in scans]
        return {"items": items, "page": page, "limit": limit, "total": total}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to fetch scan history for domain {domain_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_FETCHING_SCAN_HISTORY})
