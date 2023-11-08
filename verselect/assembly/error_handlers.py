from logging import getLogger

import orjson
import pydantic
from fastapi import FastAPI, Request, exceptions, status
from fastapi.responses import ORJSONResponse
from monite_common.exceptions import BusinessLogicError
from monite_common.serializers import orjson_dumps_to_bytes
from monite_requester.response import MoniteHTTPStatusError
from starlette.exceptions import HTTPException as StarletteHTTPException

from verselect.exceptions import ExternalRequestError

logger = getLogger(__name__)


def http_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> ORJSONResponse:
    if isinstance(exc, ExternalRequestError):
        return ORJSONResponse(content=exc.detail, status_code=exc.status_code)

    response_data = {
        "error": {
            "message": exc.detail,
        },
    }

    if exc.status_code == 422:
        response_data = exc.detail

    # Invalid API headers
    headers = exc.headers if exc.status_code == 415 else None

    return ORJSONResponse(content=response_data, status_code=exc.status_code, headers=headers)


# It is intentionally not merged with http_exception because BusinessLogicError will not always be compatible with it
def business_logic_error(
    request: Request,
    exc: BusinessLogicError,
) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
            },
        },
    )


def monite_http_status_error(
    request: Request,
    exc: MoniteHTTPStatusError,
) -> ORJSONResponse:
    if exc.propagate_errors:
        return http_exception(
            request,
            StarletteHTTPException(
                status_code=exc.response.status_code,
                detail=exc.response._get_error_message(),  # pyright: ignore[reportGeneralTypeIssues]
                headers=exc.response.headers,
            ),
        )
    return application_exception(request, exc)


def application_exception(request: Request, exc: Exception):
    response_data = {
        "error": {
            "message": "Server Error",
        },
    }

    if isinstance(exc, pydantic.ValidationError):
        # so its a response model validation error
        response_data["error"]["message"] = "Response validation error"

    status_code = getattr(exc, "status_code", 500)

    return ORJSONResponse(content=response_data, status_code=status_code)


def validation_exception_handler(request: Request, exc: exceptions.RequestValidationError) -> "ORJSONResponse":
    errors = orjson_dumps_to_bytes(exc.errors())
    logger.warning(
        "Validation error",
        extra={"pydantic_error": errors.decode()},
    )

    return ORJSONResponse({"detail": orjson.loads(errors)}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def register_errors(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception)
    app.add_exception_handler(BusinessLogicError, business_logic_error)
    app.add_exception_handler(exceptions.RequestValidationError, validation_exception_handler)
    app.add_exception_handler(MoniteHTTPStatusError, monite_http_status_error)
    app.add_exception_handler(Exception, application_exception)
