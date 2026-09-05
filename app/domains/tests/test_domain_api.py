import uuid

from conftest import next_test_domain


def test_create_domain_forbidden_for_viewer(client, viewer_headers, make_domain):
    resp = make_domain(headers=viewer_headers)
    assert resp.status_code == 403


def test_create_domain_success(client, analyst_headers, make_domain):
    resp = make_domain(headers=analyst_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] in ("PENDING", "RUNNING", "COMPLETED", "FAILED")


def test_create_duplicate_domain_returns_409(client, admin_headers, make_domain):
    name = next_test_domain()
    r1 = make_domain(name=name)
    assert r1.status_code == 201
    r2 = make_domain(name=name)
    assert r2.status_code == 409


def test_get_domain_not_found(client, viewer_headers):
    resp = client.get(f"/api/v1/domains/{uuid.uuid4()}", headers=viewer_headers)
    assert resp.status_code == 404


def test_list_domains_search_filters_by_name(client, admin_headers, make_domain):
    created = make_domain().json()
    resp = client.get("/api/v1/domains", params={"search": created["name"].split(".")[0]}, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert any(item["name"] == created["name"] for item in body["items"])


def test_delete_domain_forbidden_for_analyst(client, analyst_headers, make_domain):
    created = make_domain(headers=analyst_headers).json()
    resp = client.delete(f"/api/v1/domains/{created['id']}", headers=analyst_headers)
    assert resp.status_code == 403


def test_delete_domain_as_admin_then_not_found(client, admin_headers, make_domain):
    created = make_domain().json()
    resp = client.delete(f"/api/v1/domains/{created['id']}", headers=admin_headers)
    assert resp.status_code == 204

    resp2 = client.get(f"/api/v1/domains/{created['id']}", headers=admin_headers)
    assert resp2.status_code == 404
