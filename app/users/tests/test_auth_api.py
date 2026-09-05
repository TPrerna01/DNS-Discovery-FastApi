from sqlalchemy import delete

from conftest import run_db, next_test_email
from app.users.models import User


def _register_body(role="VIEWER"):
    return {
        "full_name": "New User",
        "email": next_test_email(),
        "password": "StrongPass123!",
        "role": role,
    }


def _delete_user(email):
    async def _delete(db):
        await db.execute(delete(User).where(User.email == email))
        await db.commit()

    run_db(_delete)


def test_login_unknown_email_returns_401(client):
    resp = client.post("/api/v1/login", json={"email": "nobody-pytest@example.com", "password": "WrongPass123!"})
    assert resp.status_code == 401


def test_login_success_returns_token(client, admin_headers):
    # admin_headers already proved admin login works during fixture setup - just recheck the shape here
    assert admin_headers["Authorization"].startswith("Bearer ")


def test_register_without_token_returns_401(client):
    resp = client.post("/api/v1/register/", json=_register_body())
    assert resp.status_code == 401


def test_register_forbidden_for_viewer(client, viewer_headers):
    resp = client.post("/api/v1/register/", json=_register_body(), headers=viewer_headers)
    assert resp.status_code == 403


def test_register_success_as_admin(client, admin_headers):
    body = _register_body("ANALYST")
    resp = client.post("/api/v1/register/", json=body, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == body["email"]
    assert data["role"] == "ANALYST"
    _delete_user(body["email"])


def test_register_duplicate_email_returns_409(client, admin_headers):
    body = _register_body("VIEWER")
    r1 = client.post("/api/v1/register/", json=body, headers=admin_headers)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/register/", json=body, headers=admin_headers)
    assert r2.status_code == 409
    _delete_user(body["email"])
