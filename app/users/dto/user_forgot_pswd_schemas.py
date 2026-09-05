from pydantic import BaseModel, model_validator
from app.core.constants import (
    INVALID_PASSWORD_LENGTH,
    PASSWORD_MISMATCH,
    INVALID_RESET_PASSWORD_DATA,
    INVALID_PASSWORD_COMPLEXITY,
    INVALID_EMAIL_DATA,
)
from app.core.utils.common_encryption_utils import CommonEncryptionUtils


class UserForgotPswdSchema(BaseModel):
    email: str

    @model_validator(mode="after")
    def validate_email(self):
        if not self.email:
            raise ValueError({"error": INVALID_EMAIL_DATA})
        return self

class UserResetPswdSchema(BaseModel):
    new_password : str
    confirm_password : str

    @model_validator(mode="after")
    def validate(self):
        if not self.new_password:
            raise ValueError({"error": INVALID_RESET_PASSWORD_DATA})
        if len(self.new_password) < 8 or len(self.new_password) > 16:
            raise ValueError({"error": INVALID_PASSWORD_LENGTH})
        if not CommonEncryptionUtils.is_password_strong(self.new_password):
            raise ValueError({"error": INVALID_PASSWORD_COMPLEXITY})
        if self.new_password != self.confirm_password:
            raise ValueError({"error": PASSWORD_MISMATCH})
        return self
