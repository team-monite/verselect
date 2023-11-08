import json
import logging
import re
import uuid
from contextlib import suppress
from logging import getLogger

from fastapi import FastAPI, Request
from monite_common.context import auth_data_var, entity_id_var, request_id_var
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..configs import X_MONITE_VERSION_HEADER_NAME

logger = getLogger(__name__)

uvicorn_logger = logging.getLogger("uvicorn.access")
# I don't see any way of covering these lambdas in tests, so I'm just ignoring them.
uvicorn_logger.addFilter(lambda record: "/metrics" not in record.getMessage())  # pragma: no cover
uvicorn_logger.addFilter(lambda record: "/readiness" not in record.getMessage())  # pragma: no cover
uvicorn_logger.addFilter(lambda record: "/liveness" not in record.getMessage())  # pragma: no cover

is_system_handler_re = re.compile("(readiness|liveness|metrics)")


async def log_request(request: Request, call_next: RequestResponseEndpoint):
    request_headers = dict(request.headers)

    curr_rid = request_headers.get("x-request-id")
    if curr_rid is None:
        curr_rid = str(uuid.uuid4())
    request_id_var.set(curr_rid)

    x_monite_auth_data = request_headers.get("x-monite-auth-data", None)
    # Conversion to proper ASCII in case the user encoded their headers using UTF-8.
    # Can get slow but is required because auth_data contains company names which
    # can contain non-ascii characters and clients can incorrectly encode their data.

    # If you wish to use orjson instead, check that we never assume that auth_data is
    # a string because orjson will emit bytes and if you decode these bytes -- you will
    # get a utf-8 string which completely defeats the purpose of this piece of code.
    if x_monite_auth_data and isinstance(x_monite_auth_data, str):
        # In case x_monite_auth_data is not json.
        with suppress(ValueError):
            x_monite_auth_data = json.dumps(json.loads(x_monite_auth_data))

    auth_data_var.set(x_monite_auth_data)
    x_monite_entity_id = request_headers.get("x-monite-entity-id", None)
    entity_id_var.set(x_monite_entity_id)

    is_need_to_log = not is_system_handler_re.findall(request.scope["path"])
    if is_need_to_log:  # pragma: no cover # It's possible to cover this but seems like it's not worth the effort.
        logger.info(
            "Request",
            extra={
                "x-service-name": request_headers.get("x-service-name", ""),
                "x-request-id": curr_rid,
                "x-monite-auth-data": request_headers.get("x-monite-auth-data", ""),
                "x-monite-version": request_headers.get(X_MONITE_VERSION_HEADER_NAME, ""),
                "x-monite-entity-id": request_headers.get("x-monite-entity-id", ""),
                "x-ignore-rbac": request_headers.get("x-ignore-rbac", ""),
                "method": request.method,
                "path": request.scope["path"],
                "url": str(request.url),
                "query_params": str(request.query_params),
                "status_code": 0,
            },
        )

    response = await call_next(request)

    if is_need_to_log:  # pragma: no cover # It's possible to cover this but seems like it's not worth the effort.
        logger.info(
            "Response",
            extra={
                "x-service-name": request_headers.get("x-service-name", ""),
                "x-request-id": curr_rid,
                "method": request.method,
                "path": request.scope["path"],
                "url": str(request.url),
                "query_params": str(request.query_params),
                "status_code": response.status_code,
            },
        )
    return response


def register(app: FastAPI):
    app.add_middleware(BaseHTTPMiddleware, dispatch=log_request)
