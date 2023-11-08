import uvicorn
from fastapi.testclient import TestClient

from verselect import create_app
from tests._resources.utils import BASIC_HEADERS
from tests._resources.versioned_app.v2021_01_01 import router as v2021_01_01_router
from tests._resources.versioned_app.v2022_01_02 import router as v2022_01_02_router
from tests._resources.versioned_app.webhooks import router as webhooks_router

versioned_app = create_app()
versioned_app.add_header_versioned_routers(v2021_01_01_router, header_value="2021-01-01")
versioned_app.add_header_versioned_routers(v2022_01_02_router, header_value="2022-02-02")
versioned_app.add_webhook_routers(webhooks_router)

client = TestClient(versioned_app, raise_server_exceptions=False, headers=BASIC_HEADERS)
client_without_headers = TestClient(versioned_app, raise_server_exceptions=True)

if __name__ == "__main__":
    uvicorn.run(versioned_app)
