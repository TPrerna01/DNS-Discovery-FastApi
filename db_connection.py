import os
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings.config import app_settings

SUPABASE_URL = app_settings.SUPABASE_URL
SUPABASE_KEY = app_settings.SUPABASE_KEY

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SQLALCHEMY_DATABASE_URL = app_settings.DATABASE_URL

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, pool_pre_ping=True )
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession,  expire_on_commit=False)

async def get_db():
    """
    Provides a SQLAlchemy database session generator.
    This generator function creates a new database session, ensures
    proper usage with context management, and guarantees the session
    is closed after use.
    :return: An instance of SQLAlchemy database session.
    """
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise