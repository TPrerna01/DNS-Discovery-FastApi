import re
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.core.constants import INVALID_DOMAIN_DATA
from app.domains.models import DomainStatus

# lowercase FQDN, at least 2 labels (so "example" alone is rejected), no leading/trailing hyphens
FQDN_REGEX = re.compile(r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$")


class DomainCreateSchema(BaseModel):
    domain: str

    @model_validator(mode="after")
    def validate_domain(self):
        name = self.domain.strip().lower()
        if not FQDN_REGEX.match(name):
            raise ValueError({"error": INVALID_DOMAIN_DATA})
        self.domain = name
        return self


class DomainResponseSchema(BaseModel):
    id: UUID
    name: str
    status: DomainStatus

    model_config = {"from_attributes": True}


class DomainListResponseSchema(BaseModel):
    items: List[DomainResponseSchema]
    page: int
    limit: int
    total: int
