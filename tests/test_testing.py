from monite_common.schemas.auth_data import MoniteAuthData

from verselect.apps import HeaderRoutingFastAPI
from verselect.testing import get_async_client
from tests._resources.utils import BASIC_HEADERS, DEFAULT_API_VERSION
from tests._resources.versioned_app.app import versioned_app


async def test__get_async_client(auth_data: MoniteAuthData):
    expected_dict = {
        "x-request-id": "0",
        "x-service-name": "testing-service",
        "x-monite-auth-data": auth_data.json(),
        "x-monite-version": "2050-11-12",
        "x-hello-header": "world",
    }
    app = HeaderRoutingFastAPI()
    async with get_async_client(
        app,
        auth_data=auth_data,
        version="2050-11-12",
        headers={"x-hello-header": "world"},
    ) as client:
        assert client._transport.app is app  # pyright: ignore[reportGeneralTypeIssues]
        assert client.base_url == "http://test"
        for key, expected_value in expected_dict.items():
            assert client.headers[key] == expected_value
        assert client._transport.raise_app_exceptions is False  # pyright: ignore[reportGeneralTypeIssues]


async def test__get_async_client__no_args__sane_defaults_are_set():
    async with get_async_client(HeaderRoutingFastAPI()) as client:
        assert client.headers.items() > {"x-request-id": "0", "x-service-name": "testing-service"}.items()


async def test__get_async_client__send_real_request(auth_data: MoniteAuthData):
    async with get_async_client(
        versioned_app,
        auth_data=auth_data,
        version=DEFAULT_API_VERSION,
        headers=BASIC_HEADERS,  # note that basic headers include version in this case but don't have to
    ) as client:
        response = await client.get("/v1")
        assert response.json() == {"my_version1": 1}
