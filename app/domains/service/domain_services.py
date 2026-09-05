from sqlalchemy.orm import Session

from app.domains.dao.domain_dao import DomainDAO as domain_dao
from app.domains.dto.domain_schemas import DomainCreateSchema
from app.domains.models import DomainStatus


class DomainService:
    """
    Handle the business logic for domain management
    """
    @staticmethod
    async def create_domain(db: Session, domain_data: DomainCreateSchema, created_by):
        return await domain_dao.create_domain(db, domain_data, created_by)

    @staticmethod
    async def get_domain(db: Session, domain_id):
        return await domain_dao.get_domain_by_id(db, domain_id)

    @staticmethod
    async def list_domains(db: Session, page: int, limit: int, status_filter: DomainStatus, search: str):
        return await domain_dao.list_domains(db, page, limit, status_filter, search)

    @staticmethod
    async def delete_domain(db: Session, domain_id):
        return await domain_dao.delete_domain(db, domain_id)
