import contextlib
from collections.abc import AsyncGenerator
from typing import Any, cast

import httpx
from fastapi import FastAPI
from httpx import AsyncClient
from monite_common.schemas.auth_data import MoniteAuthData

from .configs import X_MONITE_VERSION_HEADER_NAME


@contextlib.asynccontextmanager
async def get_async_client(
    app: FastAPI,
    auth_data: MoniteAuthData | None = None,
    version: str | None = None,
    headers: dict[str, Any] | None = None,
    raise_app_exceptions: bool = False,
) -> AsyncGenerator[AsyncClient, Any]:
    final_headers = {"x-request-id": "0", "x-service-name": "testing-service"}

    if auth_data:
        final_headers["x-monite-auth-data"] = auth_data.json()
    if version:
        final_headers[X_MONITE_VERSION_HEADER_NAME] = version
    if headers:
        final_headers.update(headers)

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers=final_headers,
        transport=httpx.ASGITransport(app=cast(Any, app), raise_app_exceptions=raise_app_exceptions),
    ) as client:
        yield client
