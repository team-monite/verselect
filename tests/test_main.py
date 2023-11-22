import re
from fastapi import APIRouter
from fastapi.testclient import TestClient

import pytest

from tests._resources.utils import BASIC_HEADERS, DEFAULT_API_VERSION
from tests._resources.versioned_app.app import (
    client_without_headers,
    client_without_headers_and_with_custom_api_version_var,
)
from verselect.apps import HeaderRoutingFastAPI
from verselect.exceptions import VerselectAppCreationError


def test__header_routing__invalid_version_format__error():
    main_app = HeaderRoutingFastAPI()
    main_app.add_header_versioned_routers(header_value=DEFAULT_API_VERSION)
    with pytest.raises(ValueError, match=re.escape("header_value should be in `%Y-%m-%d` format")):
        main_app.add_header_versioned_routers(APIRouter(), header_value="2022-01_01")


def test__header_routing_fastapi_init__routes_were_passed__should_raise_error():
    with pytest.raises(
        VerselectAppCreationError,
        match=re.escape(
            "It's prohibited to pass routes to HeaderRoutingFastAPI. "
            "Please use `add_header_versioned_routers` or `add_unversioned_routers`"
        ),
    ):
        HeaderRoutingFastAPI(routes=[1])  # pyright: ignore[reportGeneralTypeIssues]


@pytest.mark.parametrize("client", [client_without_headers, client_without_headers_and_with_custom_api_version_var])
def test__header_based_versioning(client: TestClient):
    resp = client.get("/v1", headers=BASIC_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {"my_version1": 1}
    assert resp.headers["X-API-VERSION"] == "2021-01-01"

    resp = client.get("/v1", headers=BASIC_HEADERS | {"X-API-VERSION": "2022-02-02"})
    assert resp.status_code == 200
    assert resp.json() == {"my_version2": 2}
    assert resp.headers["X-API-VERSION"] == "2022-02-02"

    resp = client.get("/v1", headers=BASIC_HEADERS | {"X-API-VERSION": "2024-02-02"})
    assert resp.status_code == 200
    assert resp.json() == {"my_version2": 2}
    assert resp.headers["X-API-VERSION"] == "2024-02-02"


def test__header_based_versioning__invalid_version_header_format__should_raise_422():
    resp = client_without_headers.get("/v1", headers=BASIC_HEADERS | {"X-API-VERSION": "2022-02_02"})
    assert resp.status_code == 422
    assert resp.json()[0]["loc"] == ["header", "x-api-version"]


def test__get_webhooks_router():
    resp = client_without_headers.post("/v1/webhooks")
    assert resp.status_code == 200
    assert resp.json() == {"saved": True}


def test__get_openapi():
    resp = client_without_headers.get("/openapi.json?version=2021-01-01")
    assert resp.status_code == 200


def test__get_openapi__nonexisting_version__error():
    resp = client_without_headers.get("/openapi.json?version=2023-01-01")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "OpenApi file of with version `2023-01-01` not found"}


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
