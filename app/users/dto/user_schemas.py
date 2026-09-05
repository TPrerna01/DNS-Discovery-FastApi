from typing import Optional
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.core.constants import INVALID_REGISTRATION_DATA, INVALID_PASSWORD_LENGTH, INVALID_PASSWORD_COMPLEXITY
from app.core.utils.common_encryption_utils import CommonEncryptionUtils
from app.users.models import UserRole


class UserCreateSchema(BaseModel):
    id: Optional[UUID] = None
    full_name: str
    email: str
    password: str
    role: UserRole = UserRole.VIEWER

    # class Config:
    #     orm_mode = True

    @model_validator(mode="after")
    def validate(self):
        full_name = self.full_name
        email = self.email
        password = self.password
        if not full_name or not email or not password:
            raise ValueError({"error" : INVALID_REGISTRATION_DATA})
        if len(password) < 8:
            raise ValueError({"error": INVALID_PASSWORD_LENGTH})
        if not CommonEncryptionUtils.is_password_strong(password):
            raise ValueError({"error": INVALID_PASSWORD_COMPLEXITY})
        return self

class UserLoginSchema(BaseModel):
    email: str
    password: str

class UserResponseSchema(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
