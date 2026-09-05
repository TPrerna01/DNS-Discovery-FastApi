import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from app.domains.dto.domain_schemas import DomainCreateSchema, DomainResponseSchema, DomainListResponseSchema
from app.domains.models import DomainStatus
from app.domains.service.domain_services import DomainService as domain_service
from app.scans.service.scan_services import ScanService as scan_service
from app.users.models import UserRole
from app.core.constants import (
    ERROR_WHILE_CREATING_DOMAIN,
    ERROR_WHILE_FETCHING_DOMAIN,
    ERROR_WHILE_DELETING_DOMAIN,
)
from db_connection import get_db

from app.core.utils.common_auth_utils import CommonAuthUtils as auth_utils

logger = logging.getLogger("app.domains")

domain_router = APIRouter(prefix="/domains")


@domain_router.get("", response_model=DomainListResponseSchema)
async def list_domains(request: Request, db: Session = Depends(get_db),
                        page: int = Query(1, ge=1),
                        limit: int = Query(20, ge=1, le=100),
                        status_filter: Optional[DomainStatus] = Query(None, alias="status"),
                        search: Optional[str] = Query(None),
                        current_user = Depends(auth_utils.get_current_active_user)):
    """
    List domains with pagination, filtering by status, and search by name.
    """
    try:
        domains, total = await domain_service.list_domains(db, page, limit, status_filter, search)
        return {"items": domains, "page": page, "limit": limit, "total": total}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to list domains")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_FETCHING_DOMAIN})


@domain_router.post("", response_model=DomainResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_domain(request: Request, domain_data: DomainCreateSchema, background_tasks: BackgroundTasks,
                        db: Session = Depends(get_db),
                        current_user = Depends(auth_utils.require_roles(UserRole.ADMIN, UserRole.ANALYST))):
    """
    Register a new domain for monitoring. Admin & Analyst only.
    A discovery scan is kicked off automatically in the background.
    """
    try:
        new_domain = await domain_service.create_domain(db, domain_data, current_user.id)
        # system-triggered, so triggered_by is None - not the analyst/admin who created the domain
        await scan_service.trigger_scan(db, new_domain.id, None, background_tasks)
        return new_domain
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to create domain: {domain_data.domain}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_CREATING_DOMAIN})


@domain_router.get("/{domain_id}", response_model=DomainResponseSchema)
async def get_domain(request: Request, domain_id: str, db: Session = Depends(get_db),
                     current_user = Depends(auth_utils.get_current_active_user)):
    """
    Retrieve a single domain by id.
    """
    try:
        return await domain_service.get_domain(db, domain_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to fetch domain {domain_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_FETCHING_DOMAIN})


@domain_router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(request: Request, domain_id: str, db: Session = Depends(get_db),
                        current_user = Depends(auth_utils.require_roles(UserRole.ADMIN))):
    """
    Permanently remove a domain. Admin only.
    """
    try:
        await domain_service.delete_domain(db, domain_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to delete domain {domain_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_DELETING_DOMAIN})
