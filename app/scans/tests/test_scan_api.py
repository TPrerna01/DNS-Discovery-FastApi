import uuid

from conftest import run_db
from app.scans.models import Scan, ScanStatus


def test_trigger_scan_domain_not_found(client, analyst_headers):
    resp = client.post(f"/api/v1/domains/{uuid.uuid4()}/scan", headers=analyst_headers)
    assert resp.status_code == 404


def test_trigger_scan_forbidden_for_viewer(client, viewer_headers, make_domain):
    created = make_domain().json()
    resp = client.post(f"/api/v1/domains/{created['id']}/scan", headers=viewer_headers)
    assert resp.status_code == 403


def test_trigger_scan_conflict_when_already_running(client, admin_headers, make_domain):
    created = make_domain().json()

    async def _force_running(db):
        db.add(Scan(domain_id=created["id"], status=ScanStatus.RUNNING))
        await db.commit()

    run_db(_force_running)

    resp = client.post(f"/api/v1/domains/{created['id']}/scan", headers=admin_headers)
    assert resp.status_code == 409


def test_scan_history_includes_the_automatic_scan(client, admin_headers, make_domain):
    created = make_domain().json()
    resp = client.get(f"/api/v1/domains/{created['id']}/scans", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
