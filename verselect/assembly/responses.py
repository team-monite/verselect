from collections.abc import Mapping, Sequence
from typing import Any, cast

from starlette import status

from verselect.responses import ErrorSchemaResponse


def set_allowed_responses(codes: Sequence[int] | Mapping[int, str]) -> dict[int | str, dict[str, Any]]:
    if isinstance(codes, list):
        codes_set = set(codes)
        codes_set.add(500)  # because no one writes perfect code 👿
        codes_set.add(405)  # Method not allowed, can be called by any method
        res = {key: value for key, value in responses.items() if key in codes_set}
    elif isinstance(codes, dict):
        codes[500] = ""
        codes[405] = ""
        res = {key: set_error_response_openapi(codes[key]) for key in responses if key in codes}
    else:
        raise TypeError(f"codes should be `list` or `dict`, found: {type(codes)!r}")

    # Fastapi type hints are invalid here
    return cast(dict[int | str, dict[str, Any]], res)


def set_error_response_openapi(description: str = "") -> dict[str, Any]:
    return {"description": description, "model": ErrorSchemaResponse}


responses: dict[int | str, Any] = {
    status.HTTP_400_BAD_REQUEST: set_error_response_openapi(),
    status.HTTP_401_UNAUTHORIZED: set_error_response_openapi(),
    status.HTTP_404_NOT_FOUND: set_error_response_openapi("Not found"),
    status.HTTP_403_FORBIDDEN: set_error_response_openapi(),
    status.HTTP_405_METHOD_NOT_ALLOWED: set_error_response_openapi(),
    status.HTTP_406_NOT_ACCEPTABLE: set_error_response_openapi(),
    status.HTTP_409_CONFLICT: set_error_response_openapi("Business logic error"),
    status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE: set_error_response_openapi(),
    status.HTTP_500_INTERNAL_SERVER_ERROR: set_error_response_openapi(),
}
