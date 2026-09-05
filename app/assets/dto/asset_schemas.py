from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.assets.models import AssetType


class AssetResponseSchema(BaseModel):
    id: UUID
    domain: str
    type: AssetType
    value: str


class AssetListResponseSchema(BaseModel):
    items: List[AssetResponseSchema]
    page: int
    limit: int
    total: int
