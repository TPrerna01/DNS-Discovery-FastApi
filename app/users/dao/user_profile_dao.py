from requests import Session
from sqlalchemy import select

from app.users.models import User
from app.core.utils.db_common_utils import CommonUtils
from app.core.constants import USER_ACCOUNT_DELETE_SUCCESSFULLY, NO_DATA_FOUND


class UserProfileHandlerDAO:

    @staticmethod
    async def delete_user_profile_dao(db:Session, current_user):
        try:
            user_query = select(User).filter(User.email==current_user)
            result = await db.execute(user_query)
            user = result.scalars().first()
            if user:
                await CommonUtils.delete_db_data(db, user)
                return {"success": True, "message": USER_ACCOUNT_DELETE_SUCCESSFULLY}
            return {"success": False, "message": NO_DATA_FOUND}
        except Exception as e:
            raise e

    @staticmethod
    async def get_user_profile_dao(db:Session, current_user):
        try:
            user_query = select(User).filter(User.email==current_user)
            result = await db.execute(user_query)
            user = result.scalars().first()
            if user:
                return {"data": user, "success": True, "message": user.email}
            return {"data": None, "success": False, "message": NO_DATA_FOUND}
        except Exception as e:
            return e
