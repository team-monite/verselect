import pytest

from tests._resources import app_for_testing_dependencies


@pytest.mark.parametrize("header", ["true", "false"])
def test__get_ignore_rbac__header_passed(header: str):
    resp = app_for_testing_dependencies.client.get("/v1/get_ignore_rbac", headers={"x-ignore-rbac": header})
    header_is_true = header.lower() == "true"
    assert resp.status_code == 200
    assert resp.json()["ignore_rbac"] is header_is_true


def test__get_ignore_rbac__header_not_passed__response_is_none():
    resp = app_for_testing_dependencies.client.get("/v1/get_ignore_rbac")
    assert resp.status_code == 200
    assert resp.json()["ignore_rbac"] is None
