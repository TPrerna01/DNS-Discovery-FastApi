from sqlalchemy import Column, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase

from datetime import datetime

class Base(DeclarativeBase):
    pass

class CoreBaseModel(Base):
    __abstract__ = True

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Core(Base):
    __abstract__ = True

    created_by = Column(Integer, ForeignKey('user.id'))
    updated_by = Column(Integer, ForeignKey('user.id'))