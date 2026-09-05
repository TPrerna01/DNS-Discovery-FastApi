from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.users.dao.user_profile_dao import UserProfileHandlerDAO as user_profile_dao


class UserProfileUpdateService:
    @staticmethod
    async def delete_user_profile_service(db:Session, current_user):
        try:
            user_profile = await user_profile_dao.delete_user_profile_dao(db, current_user)
            return user_profile
        except Exception as e:
            raise {"error": f"{str(e)}"}

    @staticmethod
    async def get_user_profile_service(db:Session, current_user):
        try:
            user = await user_profile_dao.get_user_profile_dao(db, current_user)
            return user
        except Exception as e:
            raise {"error": f"{str(e)}"}