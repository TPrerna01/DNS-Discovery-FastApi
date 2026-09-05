from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status
from fastapi import HTTPException

from app.users.dto.user_pswd_update_schemas import UserChangePswdUpdateSchema
from app.users.models import User
from app.core.utils.common_encryption_utils import CommonEncryptionUtils as AuthUtils
from app.core.utils.db_common_utils import CommonUtils
from app.core.constants import CHANGE_PASSWORD_SUCCESSFULLY, INVALID_OLD_PASSWORD_DATA


class UserChangePswdDao:
    @staticmethod
    async def post_user_change_pswd(db:Session, user_data:UserChangePswdUpdateSchema, user_email:str):
        user_query = select(User).filter(User.email == user_email)
        result = await db.execute(user_query)
        current_user = result.scalars().first()
        if not current_user or not AuthUtils.verify_hash_password(user_data.old_password, current_user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": INVALID_OLD_PASSWORD_DATA})

        current_user.password = AuthUtils.get_hash_password(user_data.password)
        await CommonUtils.commit_db_data(db, current_user)
        return {"message": CHANGE_PASSWORD_SUCCESSFULLY}
