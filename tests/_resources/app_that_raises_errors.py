import uvicorn
from fastapi import HTTPException
from httpx import Request
from monite_common.exceptions import BusinessLogicError
from monite_common.schemas import ConfigMixin, HttpsUrl
from monite_requester.response import MoniteResponse
from pydantic import BaseModel

from verselect import MoniteAPIRouter
from verselect.exceptions import ExternalRequestError, InternalRequestError
from tests._resources.utils import make_app_with_client

router = MoniteAPIRouter(enable_internal_request_headers=False)


class HttpsUrlSchema(ConfigMixin):
    https_url: HttpsUrl


@router.post("/raise_http_url_error")
def raise_http_url_error(payload: HttpsUrlSchema):
    raise NotImplementedError


@router.post("/raise_business_logic_error")
def raise_business_logic_error():
    raise BusinessLogicError("this logic is against business")


@router.post("/raise_internal_request_error")
def raise_internal_request_error():
    raise InternalRequestError("very important message")


@router.post("/raise_external_request_error")
def raise_external_request_error():
    raise ExternalRequestError(405, {"error": {"message": "Oh my external request error"}})


@router.post("/raise_monite_response_error_with_propagation")
async def raise_monite_response_error_with_propagation():
    MoniteResponse(
        {"error": {"message": "hewwo"}},
        409,
        Request("POST", "http://localhost"),
        media_type="application/json",
    ).raise_for_status(propagate_errors=True)


@router.post("/raise_monite_response_error_default")
def raise_monite_response_error_default():
    MoniteResponse(
        {"error": {"message": "hewwo"}},
        409,
        Request("POST", "http://localhost"),
        media_type="application/json",
    ).raise_for_status(propagate_errors=False)


@router.post("/raise_monite_response_error_default_with_propagation")
def raise_monite_response_error_default_with_propagation():
    MoniteResponse(
        {"error": {"message": "hewwo"}},
        409,
        Request("POST", "http://localhost"),
        media_type="application/json",
    ).raise_for_status(propagate_errors=True)


@router.post("/raise_monite_response_error_default_with_propagation_and_non_str_message")
def raise_monite_response_error_default_with_propagation_and_non_str_message():
    MoniteResponse(
        {"error": {"message": {"hewwo": ["world"]}}},
        409,
        Request("POST", "http://localhost"),
        media_type="application/json",
    ).raise_for_status(propagate_errors=True)


@router.post("/raise_regular_exception")
def raise_regular_exception():
    raise Exception("Some regular exception")  # noqa: TRY002


@router.post("/raise_pydantic_validation_error")
def raise_pydantic_validation_error():
    class SomeModel(BaseModel):
        number: int

    SomeModel.parse_obj({"number": "not a number"})


@router.post("/raise_http_validation_error")
def raise_http_validation_error():
    raise HTTPException(status_code=422, detail="HTTP Validation Error")


class NumberSchema(BaseModel):
    number: int


@router.post("/number")
def post_number(number: NumberSchema):
    raise NotImplementedError


client = make_app_with_client(versioned_routers=[router])

if __name__ == "__main__":
    uvicorn.run(client.app)
