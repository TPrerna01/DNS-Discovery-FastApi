from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status
from fastapi import HTTPException

from app.core.utils.common_mail_handling import send_mail
from app.users.dto.user_forgot_pswd_schemas import (
    UserForgotPswdSchema,
    UserResetPswdSchema,
)
from app.users.models import User
from app.core.constants import (
    INVALID_EMAIL_DATA,
    SUCESSFULLY_PASSWORD_UPDATE,
    FORGOT_PASSWORD_MESSAGE,
)
from app.core.utils.common_encryption_utils import CommonEncryptionUtils as AuthUtils
from app.core.utils.db_common_utils import CommonUtils


class UserForgotPasswordDAO:
    """
    Responsible for handling user forgot password request
    """

    @staticmethod
    async def user_forgot_password(request, db: Session, user_data: UserForgotPswdSchema):
        user_query = select(User).filter(User.email == user_data.email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": INVALID_EMAIL_DATA})

        link = f"{request.base_url}reset-password/{AuthUtils.encrypt_token(user.email)}"
        message = f"Reset Your Password By clicking on the provided link: {link}"
        await send_mail("Password reset link", message, [user.email])
        return {"message": FORGOT_PASSWORD_MESSAGE}


class UserResetPasswordDAO:
    """
    Responsible for handling user reset password request
    """

    @staticmethod
    async def user_reset_password(db: Session, user_data: UserResetPswdSchema, token: str):
        email = AuthUtils.decrypt_token(token)
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"error": "Reset link is invalid or has expired."})

        user_query = select(User).filter(User.email == email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": INVALID_EMAIL_DATA})

        user.password = AuthUtils.get_hash_password(user_data.new_password)
        await CommonUtils.commit_db_data(db, user)
        return {"message": SUCESSFULLY_PASSWORD_UPDATE}
