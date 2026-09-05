from typing import List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from app.scans.models import ScanStatus


class ScanTriggerResponseSchema(BaseModel):
    scan_id: UUID
    status: ScanStatus


class ScanResponseSchema(BaseModel):
    scan_id: UUID
    status: ScanStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ScanListResponseSchema(BaseModel):
    items: List[ScanResponseSchema]
    page: int
    limit: int
    total: int
