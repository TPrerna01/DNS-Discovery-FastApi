from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from app.core.constants import AUTHORIZATION_ERROR, TOKEN_EXPIRED_ERROR, INVALID_TOKEN_ERROR, FORBIDDEN_ROLE_ERROR
from app.core.settings.config import BaseConfig
import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt

from passlib.context import  CryptContext

from db_connection import get_db

class CommonAuthUtils:


    @staticmethod
    def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
        if expires_delta is not None:
            expires_delta = datetime.now() + expires_delta
        else:
            expires_delta = datetime.now() + timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {"exp": expires_delta, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, BaseConfig.JWT_SECRET_KEY, BaseConfig.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
        if expires_delta is not None:
            expires_delta = datetime.now() + expires_delta
        else:
            expires_delta = datetime.now() + timedelta(minutes=BaseConfig.REFRESH_TOKEN_EXPIRE_MINUTES)

        to_encode = {"exp": expires_delta, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, BaseConfig.JWT_REFRESH_SECRET_KEY, BaseConfig.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def get_current_user(authorization: str = Header(None)):
        if not authorization:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": AUTHORIZATION_ERROR})
        token = authorization.split(" ")[1] if "Bearer" in authorization else authorization
        try:
            payload = jwt.decode(token, BaseConfig.JWT_SECRET_KEY, BaseConfig.ALGORITHM)
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": TOKEN_EXPIRED_ERROR})
        except jwt.JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": INVALID_TOKEN_ERROR})

    @staticmethod
    async def get_current_active_user(authorization: str = Header(None), db: Session = Depends(get_db)):
        """
        Resolve the bearer token to the full, active User row (needed for role checks).
        """
        from app.users.models import User

        email = CommonAuthUtils.get_current_user(authorization)
        user_query = select(User).filter(User.email == email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": AUTHORIZATION_ERROR})
        return user

    @staticmethod
    def require_roles(*allowed_roles):
        """
        Dependency factory enforcing the RBAC matrix, e.g. Depends(CommonAuthUtils.require_roles(UserRole.ADMIN)).
        """
        async def _dependency(current_user=Depends(CommonAuthUtils.get_current_active_user)):
            if current_user.role not in allowed_roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": FORBIDDEN_ROLE_ERROR})
            return current_user
        return _dependency

