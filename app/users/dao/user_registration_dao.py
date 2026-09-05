import logging

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status
from fastapi import HTTPException

from app.users.models import User
from app.users.dto.user_schemas import UserCreateSchema
from app.core.utils.common_encryption_utils import CommonEncryptionUtils as AuthUtils
from app.core.utils.db_common_utils import CommonUtils
from app.core.constants import USER_ALREADY_EXISTS

logger = logging.getLogger("app.auth")


class UserRegistration:
    """
    Handle the user registration
    """
    @staticmethod
    async def create_user(db: Session, user_data: UserCreateSchema) -> User:
        user_query = select(User).filter(User.email == user_data.email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        if user:
            logger.warning(f"Registration rejected, email already exists: {user_data.email}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": USER_ALREADY_EXISTS})

        hash_password = AuthUtils.get_hash_password(user_data.password)
        new_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password=hash_password,
            role=user_data.role,
        )
        new_user = await CommonUtils.insert_db_data(db, new_user)
        logger.info(f"User registered: {user_data.email} ({user_data.role})")
        return new_user
