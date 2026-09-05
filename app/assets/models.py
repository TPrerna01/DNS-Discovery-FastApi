import uuid
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, String, UUID, Enum as SQLEnum, ForeignKey, DateTime, Index

from app.core.models import Base


class AssetType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    NS = "NS"
    MX = "MX"


class Asset(Base):
    __tablename__ = 'assets'
    __table_args__ = (
        Index('ix_assets_domain_id_type', 'domain_id', 'type'),
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID, ForeignKey('scans.id', ondelete='CASCADE'), nullable=False, index=True)
    domain_id = Column(UUID, ForeignKey('domains.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(SQLEnum(AssetType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
