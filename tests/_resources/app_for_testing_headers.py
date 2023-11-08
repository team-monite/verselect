import uvicorn

from verselect import MoniteAPIRouter
from tests._resources.utils import make_app_with_client

router_with_header_check = MoniteAPIRouter(enable_internal_request_headers=True)
router_without_header_check = MoniteAPIRouter(enable_internal_request_headers=False)


@router_with_header_check.get("/with_header_check")
def with_header_check():
    return {"Hello": "World"}


@router_without_header_check.get("/without_header_check")
def without_header_check():
    return {"Hello": "World"}


client = make_app_with_client(versioned_routers=[router_without_header_check, router_with_header_check])

if __name__ == "__main__":
    uvicorn.run(client.app)
