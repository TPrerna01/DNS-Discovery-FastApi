from fastapi.openapi.models import Response
from sqlalchemy.orm import Session
from starlette import status

from app.users.dao.user_registration_dao import UserRegistration as new_user
from app.users.dao.user_login_dao import UserLoginDAO as user_login
from app.users.dao.user_change_pswd_dao import UserChangePswdDao as user_change_pswd
from app.users.dao.user_forgot_pswd_dao import (
    UserForgotPasswordDAO as user_forgot_pswd,
    UserResetPasswordDAO as user_reset_pswd,
)
from app.users.dto.user_forgot_pswd_schemas import UserForgotPswdSchema, UserResetPswdSchema
from app.users.dto.user_pswd_update_schemas import UserChangePswdUpdateSchema
from app.users.dto.user_schemas import UserCreateSchema, UserLoginSchema
from app.core.constants import USER_CREATED_SUCCESSFULLY


class UserDataService:
    """
    Handle the business logic for user data service
    """
    @staticmethod
    async def post_new_user_data(db:Session, user_data:UserCreateSchema):
        return await new_user.create_user(db, user_data)

    @staticmethod
    async def post_login_user(db:Session, user_data:UserLoginSchema):
        return await user_login.find_by_email(db, user_data)

    @staticmethod
    async def post_change_password(db:Session, user_data:UserChangePswdUpdateSchema, user:str):
        return await user_change_pswd.post_user_change_pswd(db, user_data, user)

    @staticmethod
    async def post_forgot_password(request, db:Session, user_data:UserForgotPswdSchema):
        return await user_forgot_pswd.user_forgot_password(request, db, user_data)

    @staticmethod
    async def post_reset_password(db:Session, user_data:UserResetPswdSchema, token:str):
        return await user_reset_pswd.user_reset_password(db, user_data, token)
