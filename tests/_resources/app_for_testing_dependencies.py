import uuid
from typing import Annotated

import uvicorn
from fastapi import Depends
from monite_common.schemas.auth_data import MoniteAuthData

from verselect import MoniteAPIRouter
from verselect.dependencies.headers import get_ignore_rbac_from_headers
from verselect.dependencies.monite_auth import (
    get_auth_data,
    get_auth_data_optional,
    get_entity_id,
    get_entity_id_optional,
)
from tests._resources.utils import make_app_with_client

router = MoniteAPIRouter(enable_internal_request_headers=False)


@router.get("/get_auth_data")
def get_auth_data_route(auth_data: Annotated[MoniteAuthData, Depends(get_auth_data)]):
    return auth_data


@router.get("/get_auth_data_optional")
def get_auth_data_optional_route(auth_data: Annotated[MoniteAuthData | None, Depends(get_auth_data_optional)]):
    return auth_data if auth_data else "No auth data"


@router.get("/get_entity_id")
def get_entity_id_route(entity_id: Annotated[uuid.UUID, Depends(get_entity_id)]):
    return entity_id


@router.get("/get_entity_id_optional")
def get_entity_id_optional_route(entity_id: Annotated[uuid.UUID | None, Depends(get_entity_id_optional)]):
    return entity_id if entity_id else "No entity id"


@router.get("/get_ignore_rbac")
def get_ignore_rbac_headers(ignore_rbac: Annotated[str | None, Depends(get_ignore_rbac_from_headers)]):
    return {"ignore_rbac": ignore_rbac}


client = make_app_with_client(versioned_routers=[router])

if __name__ == "__main__":
    uvicorn.run(client.app)
