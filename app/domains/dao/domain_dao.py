from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette import status
from fastapi import HTTPException

from app.domains.models import Domain, DomainStatus
from app.domains.dto.domain_schemas import DomainCreateSchema
from app.core.utils.db_common_utils import CommonUtils
from app.core.constants import DOMAIN_ALREADY_EXISTS, DOMAIN_NOT_FOUND


class DomainDAO:
    """
    Handle the domain management data access
    """
    @staticmethod
    async def create_domain(db: Session, domain_data: DomainCreateSchema, created_by) -> Domain:
        domain_query = select(Domain).filter(Domain.name == domain_data.domain)
        result = await db.execute(domain_query)
        domain = result.scalars().first()
        if domain:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": DOMAIN_ALREADY_EXISTS})

        new_domain = Domain(name=domain_data.domain, created_by=created_by)
        return await CommonUtils.insert_db_data(db, new_domain)

    @staticmethod
    async def get_domain_by_id(db: Session, domain_id) -> Domain:
        domain_query = select(Domain).filter(Domain.id == domain_id)
        result = await db.execute(domain_query)
        domain = result.scalars().first()
        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": DOMAIN_NOT_FOUND})
        return domain

    @staticmethod
    async def list_domains(db: Session, page: int, limit: int, status_filter: DomainStatus, search: str):
        domain_query = select(Domain)
        if status_filter:
            domain_query = domain_query.filter(Domain.status == status_filter)
        if search:
            domain_query = domain_query.filter(Domain.name.ilike(f"%{search}%"))

        total_query = select(func.count()).select_from(domain_query.subquery())
        total = (await db.execute(total_query)).scalar()

        domain_query = domain_query.order_by(Domain.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await db.execute(domain_query)
        domains = result.scalars().all()
        return domains, total

    @staticmethod
    async def delete_domain(db: Session, domain_id) -> None:
        domain = await DomainDAO.get_domain_by_id(db, domain_id)
        await db.delete(domain)
        await db.commit()
