from sqlalchemy.orm import Session

from app.core.constants import DATABASE_CONNECTION_ERROR


class CommonUtils:
    """
    Common Utils handle the dynamic functions which user on multiple place in project.
    """
    @staticmethod
    async def insert_db_data(db:Session, data):
        """
        Insert data into the database, if fail raise exception.
        """
        try:
            db.add(data)
            await db.commit()
            await db.refresh(data)
            return data
        except Exception as e:
            await db.rollback()
            return {"error": f"{DATABASE_CONNECTION_ERROR}"}

    @staticmethod
    async def commit_db_data(db:Session, data: dict):
        """
        Commit data into the database, if fail raise exception.
        """
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            return {"error": f"{DATABASE_CONNECTION_ERROR}"}

    @staticmethod
    async def update_db_data(db:Session, data: dict, obj):
        """
        Update data into the database, if fail raise exception.
        handle data in the form of dict.
        """
        try:
            updated_data = data.dict(exclude_unset=True)
            for key, value in updated_data.items():
                setattr(obj, key, value)
            await db.commit()
            await db.refresh(obj)

        except Exception as e:
            await db.rollback()
            return {"error": f"{DATABASE_CONNECTION_ERROR}"}

    @staticmethod
    async def delete_db_data(db:Session, obj):
        """
        Delete data from the database, if fail raise exception.
        """
        try:
            obj.is_active = False
            await db.commit()
            await db.refresh(obj)

        except Exception as e:
            await db.rollback()
            return {"error": f"{DATABASE_CONNECTION_ERROR}"}
