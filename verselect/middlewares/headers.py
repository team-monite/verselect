import time
from datetime import date
from typing import Annotated, cast

from fastapi import FastAPI, Header, Request
from fastapi._compat import _normalize_errors
from fastapi.dependencies.utils import get_dependant, solve_dependencies
from fastapi.responses import ORJSONResponse
from monite_common.context import api_version_var
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..configs import X_MONITE_VERSION_HEADER_NAME


def _get_monite_version(x_monite_version: Annotated[date, Header(examples=["2000-08-23"])]) -> date:
    raise NotImplementedError


# We use the dependant to apply fastapi's validation to the header, making validation at middleware level
# consistent with validation and route level.
VERSION_HEADER_VALIDATION_DEPENDANT = get_dependant(path="", call=_get_monite_version)


async def enrich_headers(request: Request, call_next: RequestResponseEndpoint):
    start_time = time.perf_counter()
    # We handle monite version at middleware level because if we try to add a Dependency to all routes, it won't work:
    # we use this header for routing so the user will simply get a 404 if the header is invalid.
    x_monite_version: date | None
    if X_MONITE_VERSION_HEADER_NAME in request.headers:
        solved_result = await solve_dependencies(request=request, dependant=VERSION_HEADER_VALIDATION_DEPENDANT)
        values, errors, *_ = solved_result
        if errors:
            return ORJSONResponse(status_code=422, content=_normalize_errors(errors))
        x_monite_version = cast(date, values["x_monite_version"])
        api_version_var.set(x_monite_version)
    else:
        x_monite_version = None

    response = await call_next(request)
    end_time = time.perf_counter()
    response.headers["X-PROCESS-TIME"] = str(end_time - start_time)
    request_id = request.headers.get("X-REQUEST-ID")
    if request_id:
        response.headers["X-REQUEST-ID"] = request_id

    if x_monite_version is not None:
        # We return it because we will be returning the **matched** version, not the requested one.
        response.headers[X_MONITE_VERSION_HEADER_NAME] = x_monite_version.isoformat()

    return response


def register(app: FastAPI):
    app.add_middleware(BaseHTTPMiddleware, dispatch=enrich_headers)
