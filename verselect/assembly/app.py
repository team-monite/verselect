from collections.abc import Callable, Coroutine, Sequence
from typing import Any

from fastapi.routing import APIRoute
from starlette.responses import Response

from ..apps import HeaderRoutingFastAPI
from ..middlewares import headers, logs, msgpack, prometheus
from .endpoints import basic_ping_endpoint, healthz_endpoint
from .error_handlers import register_errors


def create_app(
    title: str = "Main API app",
    description: str = "",
    openapi_url: str = "",
    version: str = "0.1.0",
    ping_endpoint: Callable[..., Coroutine[Any, Any, Response]] = basic_ping_endpoint,
    on_startup: Sequence[Callable[[], Any]] = (),
    on_shutdown: Sequence[Callable[[], Any]] = (),
    **kwargs: Any,
) -> HeaderRoutingFastAPI:
    """Create the unversioned app from which all versioned apps will be added

    Note that its routes will be available in all versions.
    """
    app = HeaderRoutingFastAPI(
        title=title,
        description=description,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        openapi_url=openapi_url,
        version=version,
        **kwargs,
    )
    _add_middleware(app=app)
    _add_default_endpoints(app=app, ping_endpoint=ping_endpoint)
    register_errors(app)
    return app


def _add_default_endpoints(*, app: HeaderRoutingFastAPI, ping_endpoint: Callable[..., Coroutine[Any, Any, Response]]):
    liveness = APIRoute(
        path="/liveness",
        methods=["GET"],
        endpoint=healthz_endpoint,
        include_in_schema=False,
    )
    readiness = APIRoute(
        path="/readiness",
        methods=["GET"],
        endpoint=ping_endpoint,
        include_in_schema=False,
    )
    app.add_unversioned_routes(liveness, readiness)


def _add_middleware(*, app: HeaderRoutingFastAPI) -> None:
    msgpack.register(app)  # msgpack must be first
    headers.register(app)
    prometheus.register(app)
    logs.register(app)
