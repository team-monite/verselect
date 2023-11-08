from fastapi import UploadFile
from pydantic import BaseModel

from verselect import MoniteAPIRouter

router = MoniteAPIRouter(enable_internal_request_headers=False)


class FirstVersionResponseModel(BaseModel):
    my_version1: int


@router.get("", response_model=FirstVersionResponseModel)
def read_root():
    return {"my_version1": 1}


@router.post("/upload_file_with_openapi_extra", openapi_extra={"schema_name": "CreateFileRequestOpenApiExtra"})
def create_file(file: UploadFile):
    raise NotImplementedError


@router.websocket_route("/non_api_route_made_only_to_verify_that_we_can_have_non_api_routes")
def non_api_route_made_only_to_verify_that_we_can_have_non_api_routes():
    raise NotImplementedError
