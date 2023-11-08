import logging

from starlette.routing import Route
from starlette.types import Scope
from starlette_exporter import PrometheusMiddleware, from_header, handle_metrics
from starlette_exporter.middleware import get_matching_route_path

from ..apps import HeaderRoutingFastAPI
from ..configs import X_MONITE_VERSION_HEADER_NAME

logger = logging.getLogger("exporter")


# can be deleted if this MR will be accepted
# https://github.com/stephenhillier/starlette_exporter/pull/76/files
class MonitePrometheusMiddleware(PrometheusMiddleware):
    # copy-pasted from original `PrometheusMiddleware` class
    # but enriched `base_scope` with `headers`
    @staticmethod
    def _get_router_path(scope: Scope) -> str | None:  # pragma: no cover
        """Returns the original router path (with url param names) for given request."""
        if not (scope.get("endpoint", None) and scope.get("router", None)):
            return None

        root_path = scope.get("root_path", "")
        app = scope.get("app", {})

        if hasattr(app, "root_path"):
            app_root_path = getattr(app, "root_path")  # noqa: B009
            if root_path.startswith(app_root_path):
                root_path = root_path[len(app_root_path) :]

        base_scope = {
            "type": scope.get("type"),
            "path": root_path + scope.get("path", ""),
            "path_params": scope.get("path_params", {}),
            "method": scope.get("method"),
            # I added the line below
            "headers": scope.get("headers", {}),
        }

        try:
            return get_matching_route_path(
                base_scope,
                getattr(scope.get("router"), "routes"),  # noqa: B009
            )
        except Exception:  # noqa: S110, BLE001
            # unhandled path
            pass

        return None


def register(app: HeaderRoutingFastAPI):
    app.add_middleware(
        MonitePrometheusMiddleware,
        prefix="fastapi",
        always_use_int_status=True,
        group_paths=True,
        skip_paths=["/readiness", "/liveness"],
        labels={"x_monite_version": from_header(X_MONITE_VERSION_HEADER_NAME)},
    )
    app.add_unversioned_routes(
        Route(
            path="/metrics",
            endpoint=handle_metrics,
            include_in_schema=False,
        ),
    )
