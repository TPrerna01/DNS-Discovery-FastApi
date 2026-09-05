from unittest.mock import patch


def test_list_assets_requires_auth(client):
    resp = client.get("/api/v1/assets")
    assert resp.status_code == 401


def test_list_assets_filtered_by_domain_and_type(client, admin_headers, make_domain):
    async def fake_resolve(resolver, domain_name, record_type):
        return ["10 mail.example.com"] if record_type == "MX" else []

    with patch("app.scans.worker._resolve_record", side_effect=fake_resolve):
        created = make_domain().json()

    resp = client.get("/api/v1/assets", params={"domain_id": created["id"], "type": "MX"}, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["type"] == "MX"
    assert body["items"][0]["domain"] == created["name"]
    assert body["items"][0]["value"] == "10 mail.example.com"
