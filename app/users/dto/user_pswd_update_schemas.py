from pydantic import BaseModel, model_validator
from app.core.constants import INVALID_PASSWORD_LENGTH, PASSWORD_MISMATCH, INVALID_CHANGE_PASSWORD_DATA, INVALID_PASSWORD_COMPLEXITY
from app.core.utils.common_encryption_utils import CommonEncryptionUtils


class UserChangePswdUpdateSchema(BaseModel):
    old_password: str
    password: str
    confirm_password: str

    @model_validator(mode='after')
    def validate_atts(self):
        old_password = self.old_password
        password = self.password
        confirm_password = self.confirm_password
        if not all([old_password, password, confirm_password]):
            raise AssertionError({"error": INVALID_CHANGE_PASSWORD_DATA})
        if password != confirm_password:
            raise ValueError({"error": PASSWORD_MISMATCH})
        if len(password) < 8:
            raise ValueError({"error": INVALID_PASSWORD_LENGTH})
        if not CommonEncryptionUtils.is_password_strong(password):
            raise ValueError({"error": INVALID_PASSWORD_COMPLEXITY})
        return self


