from typing import Optional
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.core.constants import INVALID_REGISTRATION_DATA, INVALID_PASSWORD_LENGTH


class UserCreateSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    email: str
    password: str

    # class Config:
    #     orm_mode = True

    @model_validator(mode="after")
    def validate(self):
        name = self.name
        email = self.email
        password = self.password
        if not name or not email or not password:
            raise ValueError({"error" : INVALID_REGISTRATION_DATA})
        if len(password) < 8:
            raise ValueError({"error": INVALID_PASSWORD_LENGTH})
        return self

class UserLoginSchema(BaseModel):
    email: str
    password: str