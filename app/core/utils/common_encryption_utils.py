import re
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.core.settings.config import BaseConfig

load_dotenv()

class CommonEncryptionUtils:

    @staticmethod
    def password_context():
        return CryptContext(schemes=['bcrypt'], deprecated='auto')

    @staticmethod
    def is_password_strong(password: str) -> bool:
        return (
            re.search(r'[A-Z]', password) is not None
            and re.search(r'[a-z]', password) is not None
            and re.search(r'\d', password) is not None
            and re.search(r'[^A-Za-z0-9]', password) is not None
        )

    @staticmethod
    def get_hash_password(password: str) -> str:
        password_context = CommonEncryptionUtils.password_context()
        return password_context.hash(password)

    @staticmethod
    def verify_hash_password(password: str, hashed_pass: str) -> bool:
        password_context = CommonEncryptionUtils.password_context()
        return password_context.verify(password, hashed_pass)

    @staticmethod
    def encrypt_token(user_data: str) -> str:
        expires_delta = datetime.now() + timedelta(minutes=2)

        to_encode = {"exp": expires_delta, "sub": str(user_data)}
        hashed_token = jwt.encode(to_encode, BaseConfig.JWT_SECRET_KEY, algorithm=BaseConfig.ALGORITHM)
        return hashed_token

    @staticmethod
    def decrypt_token(token: str) -> str:
        try:
            payload = jwt.decode(token, BaseConfig.JWT_SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
            return payload["sub"]
        except jwt.JWTError:
            return None


# print(CommonEncryptionUtils.decrypt_token(CommonEncryptionUtils.encrypt_token("rnatasa@yopmail.com")))