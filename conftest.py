import asyncio
import itertools

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from starlette.testclient import TestClient

from main import app
from app.core.settings.config import app_settings
from app.users.models import User, UserRole
from app.domains.models import Domain
from app.core.utils.common_encryption_utils import CommonEncryptionUtils

TEST_PASSWORD = "TestPass123!"

_EMAIL_DOMAINS = ["yopmail.com", "dripzgaming.com"]
_email_counter = itertools.count(1)
_email_domain_cycle = itertools.cycle(_EMAIL_DOMAINS)


def next_test_email() -> str:
    return f"test{next(_email_counter)}@{next(_email_domain_cycle)}"

REAL_TEST_DOMAINS = ["w3schools.com", "medium.com", "fastapi.tiangolo.com", "python.org", "github.com"]
_domain_cycle = itertools.cycle(REAL_TEST_DOMAINS)


def next_test_domain() -> str:
    return next(_domain_cycle)

TEST_ENGINE = create_async_engine(app_settings.DATABASE_URL, poolclass=NullPool)
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, class_=AsyncSession, expire_on_commit=False)


def run_db(coro_fn):
    """Run a one-off DB coroutine from synchronous test/fixture code."""
    async def _runner():
        async with TestSessionLocal() as db:
            return await coro_fn(db)

    return asyncio.run(_runner())


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _create_test_user(role: UserRole) -> str:
    email = next_test_email()

    async def _create(db):
        db.add(User(full_name="Pytest User", email=email,
                   password=CommonEncryptionUtils.get_hash_password(TEST_PASSWORD), role=role))
        await db.commit()

    run_db(_create)
    return email


def _delete_test_user(email: str):
    async def _delete(db):
        await db.execute(delete(User).where(User.email == email))
        await db.commit()

    run_db(_delete)


def _role_headers_fixture(role: UserRole, client):
    email = _create_test_user(role)
    token = client.post("/api/v1/login", json={"email": email, "password": TEST_PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


@pytest.fixture(scope="session")
def admin_headers(client):
    headers, email = _role_headers_fixture(UserRole.ADMIN, client)
    yield headers
    _delete_test_user(email)


@pytest.fixture(scope="session")
def analyst_headers(client):
    headers, email = _role_headers_fixture(UserRole.ANALYST, client)
    yield headers
    _delete_test_user(email)


@pytest.fixture(scope="session")
def viewer_headers(client):
    headers, email = _role_headers_fixture(UserRole.VIEWER, client)
    yield headers
    _delete_test_user(email)


@pytest.fixture
def make_domain(client, admin_headers):
    """Factory fixture: creates a domain (via the API) and deletes it after the test."""
    created_names = []

    def _make(headers=None, name=None):
        name = name or next_test_domain()
        resp = client.post("/api/v1/domains", json={"domain": name}, headers=headers or admin_headers)
        created_names.append(name)
        return resp

    yield _make

    async def _cleanup(db):
        for name in created_names:
            await db.execute(delete(Domain).where(Domain.name == name))
        await db.commit()

    run_db(_cleanup)
