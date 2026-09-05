import uuid
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, String, UUID, Enum as SQLEnum, ForeignKey, DateTime

from app.core.models import Base


class DomainStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Domain(Base):
    __tablename__ = 'domains'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    status = Column(
        SQLEnum(DomainStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DomainStatus.PENDING,
    )
    created_by = Column(UUID, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
