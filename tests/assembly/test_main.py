from typing import Annotated

import pytest
from fastapi import File, UploadFile

from verselect import MoniteAPIRouter, create_app
from verselect.exceptions import MoniteAppCreationError
from tests._resources import app_for_testing_headers


def test__check_headers__enabled():
    response = app_for_testing_headers.client.get("/v1/with_header_check")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {"loc": ["header", "x-service-name"], "msg": "field required", "type": "value_error.missing"},
            {"loc": ["header", "x-request-id"], "msg": "field required", "type": "value_error.missing"},
        ],
    }

    response = app_for_testing_headers.client.get(
        "/v1/with_header_check",
        headers={"x-service-name": "test", "x-request-id": "test"},
    )
    assert response.status_code == 200


def test__check_headers__disabled():
    response = app_for_testing_headers.client.get("/v1/without_header_check")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


@pytest.mark.parametrize(
    "file_type",
    [UploadFile, Annotated[bytes, File()]],
)
def test__create_app_with_file__not_renamed__error(file_type: type):
    router = MoniteAPIRouter(enable_internal_request_headers=False)

    @router.post("/upload_file", include_in_schema=False)
    def upload_file(file: file_type):  # pyright: ignore[reportGeneralTypeIssues] # Variable in typehint
        raise NotImplementedError

    error = (
        "There is a `File` or `UploadFile` field in the route with `route.name='upload_file'` "
        "and `route.path='/v1/upload_file'` and no custom `schema_name` provided. Please "
        'pass `openapi_extra={"schema_name": "SCHEMA_NAME_HERE"}`'
    )
    app = create_app()
    with pytest.raises(
        MoniteAppCreationError,
        match=error,
    ):
        app.add_header_versioned_routers(router, header_value="2023-02-07")


@pytest.mark.parametrize(
    "file_type",
    [UploadFile, Annotated[bytes, File()]],
)
def test__create_app_with_file__renamed(file_type: type):
    router = MoniteAPIRouter(enable_internal_request_headers=False)

    def upload_file(file: file_type):  # pyright: ignore[reportGeneralTypeIssues] # Variable in typehint
        raise NotImplementedError

    router.add_api_route(
        path="/upload_file",
        endpoint=upload_file,
        methods=["POST"],
        openapi_extra={"schema_name": "MyCreateFileSchema"},
    )
    app = create_app()
    app.add_header_versioned_routers(router, header_value="2023-02-07")
    body_field = app.routes[-1].body_field  # pyright: ignore[reportGeneralTypeIssues]
    assert body_field.type_.__name__ == "MyCreateFileSchema"


def test__create_sub_app__empty_endpoints__should_not_fail():
    empty_router = MoniteAPIRouter(enable_internal_request_headers=False)

    @empty_router.post("/upload_file", openapi_extra={"schema_name": "MyCreateFileSchema"}, include_in_schema=False)
    def upload_file():
        raise NotImplementedError

    app = create_app()
    app.add_header_versioned_routers(
        MoniteAPIRouter(enable_internal_request_headers=False),
        empty_router,
        header_value="2023-02-07",
    )


def test__create_app_with_routes__error():
    with pytest.raises(
        MoniteAppCreationError,
        match="Please use `add_header_versioned_routers` or `add_unversioned_routers`",
    ):
        create_app(routes=[])
