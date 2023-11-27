from contextvars import ContextVar

import uvicorn
from fastapi.testclient import TestClient

from tests._resources.utils import BASIC_HEADERS
from tests._resources.versioned_app.v2021_01_01 import router as v2021_01_01_router
from tests._resources.versioned_app.v2022_01_02 import router as v2022_01_02_router
from tests._resources.versioned_app.webhooks import router as webhooks_router
from verselect import HeaderRoutingFastAPI

versioned_app = HeaderRoutingFastAPI()
versioned_app.add_header_versioned_routers(v2021_01_01_router, header_value="2021-01-01")
versioned_app.add_header_versioned_routers(v2022_01_02_router, header_value="2022-02-02")
versioned_app.add_unversioned_routers(webhooks_router)

versioned_app_with_custom_api_version_var = HeaderRoutingFastAPI(api_version_var=ContextVar("My api version"))
versioned_app_with_custom_api_version_var.add_header_versioned_routers(v2021_01_01_router, header_value="2021-01-01")
versioned_app_with_custom_api_version_var.add_header_versioned_routers(v2022_01_02_router, header_value="2022-02-02")
versioned_app_with_custom_api_version_var.add_unversioned_routers(webhooks_router)

client = TestClient(versioned_app, raise_server_exceptions=False, headers=BASIC_HEADERS)
client_without_headers = TestClient(versioned_app)
client_without_headers_and_with_custom_api_version_var = TestClient(versioned_app_with_custom_api_version_var)

if __name__ == "__main__":
    uvicorn.run(versioned_app)
