import os
import environ
from pathlib import Path
from pydantic.v1 import BaseSettings
from fastapi_mail import ConnectionConfig

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

env = environ.Env()
if ENV_FILE.exists():
    env.read_env(str(ENV_FILE))

class Settings(BaseSettings):
    # Supabase & Database Core Connections
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DATABASE_URL: str

    ALGORITHM: str
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.mail.yahoo.com"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True

    class Config:
        from_attributes = True
        env_file = str(ENV_FILE)

app_settings = Settings()

class BaseConfig:
    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

    ALGORITHM = app_settings.ALGORITHM
    JWT_SECRET_KEY = app_settings.JWT_SECRET_KEY
    JWT_REFRESH_SECRET_KEY = app_settings.JWT_REFRESH_SECRET_KEY

    mail_conf = ConnectionConfig(
        MAIL_USERNAME=app_settings.MAIL_USERNAME,
        MAIL_PASSWORD=app_settings.MAIL_PASSWORD,
        MAIL_FROM=app_settings.MAIL_FROM,
        MAIL_PORT=app_settings.MAIL_PORT,
        MAIL_SERVER=app_settings.MAIL_SERVER,
        MAIL_STARTTLS=app_settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=app_settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True
    )