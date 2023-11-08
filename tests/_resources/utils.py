import uuid

from fastapi.testclient import TestClient

from verselect import MoniteAPIRouter, create_app

DEFAULT_API_VERSION = "2021-01-01"
BASIC_HEADERS = {"x-request-id": str(uuid.uuid4()), "x-service-name": "fwefwe", "x-monite-version": DEFAULT_API_VERSION}


def make_app(
    versioned_routers: list[MoniteAPIRouter],
    header_value: str = DEFAULT_API_VERSION,
):
    main_app = create_app()
    main_app.add_header_versioned_routers(*versioned_routers, header_value=header_value)
    return main_app


def make_app_with_client(
    versioned_routers: list[MoniteAPIRouter],
) -> TestClient:
    main_app = make_app(versioned_routers)
    return TestClient(main_app, raise_server_exceptions=False, headers={"x-monite-version": DEFAULT_API_VERSION})
