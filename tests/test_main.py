import re

import pytest

from tests._resources.app_with_duplicate_schemas import router
from tests._resources.cadwyn_versioned_app.app import client_without_headers as cadwyn_client_without_headers
from tests._resources.utils import BASIC_HEADERS, make_app
from tests._resources.versioned_app.app import client_without_headers


def test__header_routing__invalid_version_format__error():
    main_app = make_app(versioned_routers=[])
    with pytest.raises(ValueError, match=re.escape("header_value should be in `%Y-%m-%d` format")):
        main_app.add_header_versioned_routers(router, header_value="2022-01_01")


def test__header_based_versioning():
    resp = client_without_headers.get("/v1", headers=BASIC_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {"my_version1": 1}
    assert resp.headers["X-MONITE-VERSION"] == "2021-01-01"

    resp = client_without_headers.get("/v1", headers=BASIC_HEADERS | {"x-monite-version": "2022-02-02"})
    assert resp.status_code == 200
    assert resp.json() == {"my_version2": 2}
    assert resp.headers["X-MONITE-VERSION"] == "2022-02-02"

    resp = client_without_headers.get("/v1", headers=BASIC_HEADERS | {"x-monite-version": "2024-02-02"})
    assert resp.status_code == 200
    assert resp.json() == {"my_version2": 2}
    assert resp.headers["X-MONITE-VERSION"] == "2024-02-02"


def test__header_based_versioning__with_cadwyn__should_work_the_same_as_without_it():
    resp = cadwyn_client_without_headers.get("/v1", headers=BASIC_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {"my_version1": 1}
    assert resp.headers["X-MONITE-VERSION"] == "2021-01-01"

    resp = cadwyn_client_without_headers.get("/v1", headers=BASIC_HEADERS | {"x-monite-version": "2022-02-02"})
    assert resp.status_code == 200
    assert resp.json() == {"my_version2": 2}
    assert resp.headers["X-MONITE-VERSION"] == "2022-02-02"

    resp = cadwyn_client_without_headers.get("/v1", headers=BASIC_HEADERS | {"x-monite-version": "2024-02-02"})
    assert resp.status_code == 200
    assert resp.json() == {"my_version2": 2}
    assert resp.headers["X-MONITE-VERSION"] == "2024-02-02"


def test__header_based_versioning__invalid_version_header_format__should_raise_422():
    resp = client_without_headers.get("/v1", headers=BASIC_HEADERS | {"x-monite-version": "2022-02_02"})
    assert resp.status_code == 422
    assert resp.json() == [
        {"loc": ["header", "x-monite-version"], "msg": "invalid date format", "type": "value_error.date"},
    ]


def test__get_webhooks_router():
    resp = client_without_headers.post("/v1/webhooks")
    assert resp.status_code == 200
    assert resp.json() == {"saved": True}


def test__get_openapi():
    resp = client_without_headers.get("/openapi.json?version=2021-01-01")
    assert resp.status_code == 200
    assert resp.json()["components"]["schemas"]["CreateFileRequestOpenApiExtra"]


def test__get_openapi__nonexisting_version__error():
    resp = client_without_headers.get("/openapi.json?version=2023-01-01")
    assert resp.status_code == 404
    assert resp.json()["error"]["message"] == "OpenApi file of with version `2023-01-01` not found"


def test__get_docs__all_versions():
    resp = client_without_headers.get("/docs")
    assert resp.status_code == 200
    assert "http://testserver/docs?version=2022-02-02" in resp.text
    assert "http://testserver/docs?version=2021-01-01" in resp.text
    assert "http://testserver/docs?version=unversioned" in resp.text


# I wish we could check it properly but it's a dynamic page and I'm not in the mood of adding selenium
def test__get_docs__specific_version():
    resp = client_without_headers.get("/docs?version=2022-01-01")
    assert resp.status_code == 200


def test__get_metrics():
    resp = client_without_headers.get("/metrics")
    assert resp.status_code == 200
    assert 'fastapi_requests_in_progress{app_name="starlette",method="GET",x_monite_version=""} 1.0' in resp.text


def test__get_webhooks_with_redirect():
    resp = client_without_headers.post("/v1/webhooks/")
    assert resp.status_code == 200
    assert resp.json() == {"saved": True}


def test__get_webhooks_as_partial_because_of_method():
    resp = client_without_headers.patch("/v1/webhooks")
    assert resp.status_code == 405


def test__empty_root():
    resp = client_without_headers.get("/")
    assert resp.status_code == 404
