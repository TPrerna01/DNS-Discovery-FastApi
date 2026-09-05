import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from app.users.dao.user_change_pswd_dao import UserChangePswdDao
from app.users.dto.user_forgot_pswd_schemas import UserForgotPswdSchema, UserResetPswdSchema
from app.users.dto.user_pswd_update_schemas import UserChangePswdUpdateSchema
from app.users.dto.user_schemas import UserCreateSchema, UserLoginSchema, UserResponseSchema
from app.users.models import UserRole
from app.core.utils.common_mail_handling import send_mail
from app.core.constants import (
    ERROR_WHILE_CREATING_NEW_DATA,
    USER_CREATED_SUCCESSFULLY,
    ERROR_WHILE_LOGIN,
    ERROR_WHILE_CHANGE_PASSWORD_DATA,
    ERROR_WHILE_FORGETTING_PASSWORD,
    ERROR_WHILE_RESETING_PASSWORD,
    ERROR_WHILE_DELETING_USER_DATA,
    ERROR_WHILE_FETCHING_USER_DATA,
)
from db_connection import get_db

from app.users.service.user_data_services import UserDataService as user_data_service
from app.users.service.user_profile_services import UserProfileUpdateService as user_profile_creation
from app.core.utils.common_auth_utils import CommonAuthUtils as auth_utils

logger = logging.getLogger("app.auth")

auth_router = APIRouter()


@auth_router.post("/register/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def registration(request:Request, user_data:UserCreateSchema, db:Session = Depends(get_db),
                        current_user = Depends(auth_utils.require_roles(UserRole.ADMIN))):
    """
    Create a new user. Admin only.
    """
    try:
        return await user_data_service.post_new_user_data(db, user_data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to register user {user_data.email}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_CREATING_NEW_DATA})

@auth_router.post("/login")
async def login(request:Request, user_data:UserLoginSchema, db:Session = Depends(get_db)):
    """
    Login a user
    :return: token
    """
    try:
        return await user_data_service.post_login_user(db, user_data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Login attempt errored for {user_data.email}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_LOGIN})


@auth_router.post("/change-password/")
async def change_password(request:Request, user_data:UserChangePswdUpdateSchema, db:Session = Depends(get_db),
                    current_user:dict = Depends(auth_utils.get_current_user)):
    """
    Change password of a user
    """
    try:
        return await user_data_service.post_change_password(db, user_data, current_user)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Change-password errored for {current_user}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_CHANGE_PASSWORD_DATA})

@auth_router.post("/forgot-password/")
async def forgot_password(request:Request, user_data:UserForgotPswdSchema,
                    db:Session = Depends(get_db)):
    """
    Handle the forgot password request and sent mail
    """
    try:
        return await user_data_service.post_forgot_password(request, db, user_data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Forgot-password errored for {user_data.email}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_FORGETTING_PASSWORD})

@auth_router.post("/reset-password/{token}/")
async def reset_password(request:Request, user_data:UserResetPswdSchema,
                         db:Session = Depends(get_db), token:str = None):
    """
    Reset password of a user
    """
    try:
        return await user_data_service.post_reset_password(db, user_data, token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Reset-password errored")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": ERROR_WHILE_RESETING_PASSWORD})

@auth_router.delete("/delete-user-profile/")
async def delete_user_profile(request:Request, db:Session=Depends(get_db),
                              current_user=Depends(auth_utils.get_current_user)):
    try:
        return await user_profile_creation.delete_user_profile_service(db, current_user)
    except Exception as e:
        logger.exception(f"Failed to delete profile for {current_user}")
        raise HTTPException(status_code=500,
                            detail={"error": f"{ERROR_WHILE_DELETING_USER_DATA}"})

@auth_router.get("/profile/")
async def get_user_profile(request:Request,
                     db:Session=Depends(get_db), current_user=Depends(auth_utils.get_current_user)):
    try:
        return await user_profile_creation.get_user_profile_service(db, current_user)
    except Exception as e:
        logger.exception(f"Failed to fetch profile for {current_user}")
        raise HTTPException(status_code=500,
                            detail={"error": f"{ERROR_WHILE_FETCHING_USER_DATA}"})
