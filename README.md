# verselect

Header-based routing for API versioning in FastAPI

Battle-tested at Monite in production. 

## Warning

The up-to-date version of verselect is now a part of [Cadwyn](https://github.com/zmievsa/cadwyn). Using it instead is recommended.

## Explanation

At Monite, we are using header-based versioning, meaning that the client has to specify the version of the API it wants to use in the header in the YYYY-MM-DD format.

The issue with this approach is that when releasing a new API version, we need to support it in every service, which is a lot of work. `verselect` resolves this issue.

## How it works

`verselect` supports waterflowing the requests to the latest version of the API if the request header doesn't match any of the versions.

If the app has two versions: `2022-01-02` and `2022-01-05`, and the request header
is `2022-01-03`, then the request will be routed to `2022-01-02` version as it the closest
version, but lower than the request header.

Exact match is always preferred over partial match and a request will never be
matched to the higher versioned route

Also non-versioned routes and routers can be added for the endpoints, like webhooks

## Usage

```python
from contextvars import ContextVar
from datetime import date

from fastapi import APIRouter
import uvicorn
from starlette.responses import Response

from verselect import HeaderRoutingFastAPI

api_version_var: ContextVar[date] = ContextVar("api_version")
router = APIRouter()
webhook_router = APIRouter()


@router.get("/users")
def users():
    return Response(f"Hello from {api_version_var.get()}", media_type="text/plain")

@webhook_router.get("/webhooks")
def webhooks():
    return Response("webhooks", media_type="text/plain")

versions = [
    "2022-01-10",
    "2022-02-11",
    "1998-11-15",
    "2022-03-12",
    "2027-11-15",
    "2022-04-14",
]
mixed_hosts_app = HeaderRoutingFastAPI(
    api_version_header_name="X-API-Version",
    api_version_var=api_version_var,
)
for version in versions:
    mixed_hosts_app.add_header_versioned_routers(
        router,
        header_value=version,
    )
    mixed_hosts_app.add_unversioned_routers(webhook_router)

if __name__ == '__main__':
    uvicorn.run(mixed_hosts_app)
```

By running the app, at <http://localhost:8000/docs> you will see a dashboard with the available versions.

More examples can be found in the `tests._resources` folder.
