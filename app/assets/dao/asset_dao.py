from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.assets.models import Asset, AssetType
from app.domains.models import Domain


class AssetDAO:
    """
    Handle the asset inventory data access
    """
    @staticmethod
    async def list_assets(db: Session, page: int, limit: int, domain_id: str, record_type: AssetType):
        asset_query = select(Asset, Domain.name).join(Domain, Asset.domain_id == Domain.id)
        if domain_id:
            asset_query = asset_query.filter(Asset.domain_id == domain_id)
        if record_type:
            asset_query = asset_query.filter(Asset.type == record_type)

        total_query = select(func.count()).select_from(asset_query.subquery())
        total = (await db.execute(total_query)).scalar()

        asset_query = asset_query.order_by(Asset.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await db.execute(asset_query)
        return result.all(), total
