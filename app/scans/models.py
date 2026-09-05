import uuid
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, String, UUID, Enum as SQLEnum, ForeignKey, DateTime

from app.core.models import Base


class ScanStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Scan(Base):
    __tablename__ = 'scans'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    domain_id = Column(UUID, ForeignKey('domains.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(
        SQLEnum(ScanStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ScanStatus.PENDING,
    )
    triggered_by = Column(UUID, ForeignKey('users.id'), nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
