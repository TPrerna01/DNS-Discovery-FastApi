import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from app.assets.dto.asset_schemas import AssetListResponseSchema
from app.assets.models import AssetType
from app.assets.service.asset_services import AssetService as asset_service
from app.core.constants import ERROR_WHILE_FETCHING_ASSETS
from db_connection import get_db

from app.core.utils.common_auth_utils import CommonAuthUtils as auth_utils

logger = logging.getLogger("app.assets")

asset_router = APIRouter(prefix="/assets")


@asset_router.get("", response_model=AssetListResponseSchema)
async def list_assets(request: Request, db: Session = Depends(get_db),
                      page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                      domain_id: Optional[str] = Query(None),
                      record_type: Optional[AssetType] = Query(None, alias="type"),
                      current_user = Depends(auth_utils.get_current_active_user)):
    """
    List discovered assets across all domains, filterable by domain and record type.
    """
    try:
        rows, total = await asset_service.list_assets(db, page, limit, domain_id, record_type)
        items = [{"id": asset.id, "domain": domain_name, "type": asset.type, "value": asset.value}
                for asset, domain_name in rows]
        return {"items": items, "page": page, "limit": limit, "total": total}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to list assets")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_FETCHING_ASSETS})
