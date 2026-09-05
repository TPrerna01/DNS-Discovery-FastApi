import pytest
from pydantic import ValidationError

from app.users.dto.user_schemas import UserCreateSchema


def test_strong_password_accepted():
    user = UserCreateSchema(full_name="Jane", email="jane@example.com", password="StrongPass123!", role="VIEWER")
    assert user.password == "StrongPass123!"


def test_password_too_short_rejected():
    with pytest.raises(ValidationError):
        UserCreateSchema(full_name="Jane", email="jane@example.com", password="Sh0rt!", role="VIEWER")


def test_password_missing_complexity_rejected():
    with pytest.raises(ValidationError):
        UserCreateSchema(full_name="Jane", email="jane@example.com", password="alllowercase1", role="VIEWER")


def test_default_role_is_viewer():
    user = UserCreateSchema(full_name="Jane", email="jane@example.com", password="StrongPass123!")
    assert user.role == "VIEWER"
