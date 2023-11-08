from typing import Annotated
from uuid import UUID

import orjson
import pydantic
from fastapi import Header, HTTPException
from monite_common.schemas.auth_data import MoniteAuthData

UUID_EXAMPLE = "9d2b4c8f-2087-4738-ba91-7359683c49a4"
AUTH_DATA = '{"partner":{"id": "' + UUID_EXAMPLE + '"}, "project":{"id": "' + UUID_EXAMPLE + '"}}'


def _parse_auth_data(x_monite_auth_data: str) -> MoniteAuthData:
    try:
        # this block is for api-gateway
        # see this commit, which is actual when Im writing it
        # https://gitlab.monite.com/monite/infra/kong-monite-auth-plugin/-/blob/475defde66ee2c7a8e4af97d3b8987dbeb66232e/kong/plugins/monite-auth/handler.lua#L96
        # kong plugin engine sets headers this way
        # here Im waiting for an example from above
        x_monite_auth_data_d = orjson.loads(x_monite_auth_data.strip("'"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="x-monite-auth-data should be a json string") from e
    try:
        MoniteAuthData.validate(x_monite_auth_data_d)
    except pydantic.ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    return MoniteAuthData(**x_monite_auth_data_d)


async def get_auth_data(
    x_monite_auth_data: Annotated[
        str,
        Header(description="auth data from token from auth-n-settings service", examples=[AUTH_DATA]),
    ],
) -> MoniteAuthData:
    return _parse_auth_data(x_monite_auth_data)


async def get_auth_data_optional(
    x_monite_auth_data: Annotated[
        str | None,
        Header(
            description="auth data from token from auth-n-settings service",
            examples=[AUTH_DATA],
        ),
    ] = None,
) -> MoniteAuthData | None:
    if not x_monite_auth_data:
        return None
    return _parse_auth_data(x_monite_auth_data)


async def get_entity_id(
    x_monite_entity_id: Annotated[
        UUID,
        Header(description="The ID of the entity that owns the requested resource.", examples=[UUID_EXAMPLE]),
    ],
) -> UUID:
    return x_monite_entity_id


async def get_entity_id_optional(
    x_monite_entity_id: Annotated[
        UUID | None,
        Header(description="The ID of the entity that owns the requested resource.", examples=[UUID_EXAMPLE]),
    ] = None,
) -> UUID | None:
    return x_monite_entity_id
