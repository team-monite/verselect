from tests._resources.versioned_app.app import client_without_headers


def test__ping():
    resp = client_without_headers.get("/readiness")
    assert resp.status_code == 200
    assert resp.text == "pong"


def test__healthz():
    resp = client_without_headers.get("/liveness")
    assert resp.status_code == 200
    assert resp.json() == {"temperature": 36.6}
