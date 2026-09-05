import logging

from sqlalchemy import select

from app.users.models import User
from sqlalchemy.orm import Session
from fastapi import HTTPException
from starlette import status

from app.users.dto.user_schemas import UserLoginSchema
from app.core.utils.common_encryption_utils import CommonEncryptionUtils as AuthUtils
from app.core.utils.common_auth_utils import CommonAuthUtils as commonAuthUtils
from app.core.settings.config import BaseConfig
from app.core.constants import INVALID_USER_DATA

logger = logging.getLogger("app.auth")


class UserLoginDAO:

    @staticmethod
    async def find_by_email(db:Session, user_data:UserLoginSchema):
        user_query = select(User).filter(User.email == user_data.email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        if user and user.is_active and AuthUtils.verify_hash_password(user_data.password, user.password):
            logger.info(f"Login successful for {user_data.email}")
            return {
                "access_token": commonAuthUtils.create_access_token(user.email),
                "refresh_token": commonAuthUtils.create_refresh_token(user.email),
                "token_type": "bearer",
                "expires_in": BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }
        logger.warning(f"Login failed for {user_data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": INVALID_USER_DATA})
