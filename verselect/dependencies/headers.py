from typing import Annotated

from fastapi import Depends, Header

FIXED_UUID_EXAMPLE = "9d2b4c8f-2087-4738-ba91-7359683c49a4"


async def get_service_name_from_headers(
    x_service_name: Annotated[str, Header(description="Client name. Helps to trace logs", examples=["swagger"])],
):
    return x_service_name


async def internal_request_headers(
    x_request_id: Annotated[
        str,
        Header(description="Id of a request. Helps to trace logs", examples=[FIXED_UUID_EXAMPLE]),
    ],
    x_service_name: Annotated[str, Depends(get_service_name_from_headers)],
):
    pass


async def get_ignore_rbac_from_headers(
    x_ignore_rbac: Annotated[
        str | None,
        Header(description="Ignore rbac for internal communication."),
    ] = None,
    ignore_rbac: Annotated[
        str | None,
        Header(description="Old and deprecated ignore rbac for internal communication. Use X-Ignore-Rbac instead."),
    ] = None,
):
    if x_ignore_rbac:
        return x_ignore_rbac.lower() == "true"
    return ignore_rbac
