from sqlalchemy.orm import Session

from app.assets.dao.asset_dao import AssetDAO as asset_dao
from app.assets.models import AssetType


class AssetService:
    """
    Handle the business logic for the asset inventory
    """
    @staticmethod
    async def list_assets(db: Session, page: int, limit: int, domain_id: str, record_type: AssetType):
        return await asset_dao.list_assets(db, page, limit, domain_id, record_type)
