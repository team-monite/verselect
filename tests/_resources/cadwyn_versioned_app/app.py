import uvicorn
from cadwyn import generate_versioned_routers
from fastapi.testclient import TestClient

from verselect import MoniteAPIRouter, create_app
from verselect.configs import X_MONITE_VERSION_HEADER_VALUE_FORMAT
from tests._resources.cadwyn_versioned_app import latest
from tests._resources.cadwyn_versioned_app.versions import version_bundle

router = MoniteAPIRouter(enable_internal_request_headers=False)


@router.get("", response_model=latest.ResponseModel)
async def read_root():
    return {"my_version1": 1, "my_version2": 2}


main_app = create_app()
root_router = MoniteAPIRouter(
    prefix="",  # prefix will be added from `routers`
    enable_internal_request_headers=False,
)
root_router.include_router(router)

router_versions = generate_versioned_routers(
    router=root_router,
    versions=version_bundle,
    latest_schemas_module=latest,
)
for version, router in router_versions.items():
    main_app.add_header_versioned_routers(
        router,
        header_value=version.strftime(X_MONITE_VERSION_HEADER_VALUE_FORMAT),
    )

client_without_headers = TestClient(main_app, raise_server_exceptions=True)

if __name__ == "__main__":
    uvicorn.run(main_app)
