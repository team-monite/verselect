from contextvars import ContextVar
from datetime import date, datetime
from logging import getLogger
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.params import Depends as DependsType
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates
from starlette.routing import BaseRoute, Route

from verselect.routing import VERSION_HEADER_FORMAT

from .middleware import HeaderVersioningMiddleware, _get_api_version_dependency
from .routing import RootHeaderAPIRouter

CURR_DIR = Path(__file__).resolve()
logger = getLogger(__name__)


class HeaderRoutingFastAPI(FastAPI):
    templates = Jinja2Templates(directory=CURR_DIR.parent / "docs")

    def __init__(
        self,
        *args: Any,
        api_version_header_name: str = "X-API-VERSION",
        api_version_var: ContextVar[date] | ContextVar[date | None] | None = None,
        routes: list[BaseRoute] | None = None,
        docs_url: str | None = "/docs",
        redoc_url: None = None,
        openapi_url: str | None = "/openapi.json",
        default_response_class: type[Response] = JSONResponse,
        responses: Dict[int | str, Dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        dependencies: Sequence[DependsType] | None = None,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        callbacks: List[BaseRoute] | None = None,
        **kwargs: Any,
    ):
        if api_version_var is None:
            api_version_var = ContextVar("api_header_version")
        self.api_version_var = api_version_var
        super().__init__(*args, **kwargs, openapi_url=None, docs_url=None, redoc_url=None)
        self.router: RootHeaderAPIRouter = RootHeaderAPIRouter(
            routes=self.routes,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            default_response_class=default_response_class,
            dependencies=dependencies,
            callbacks=callbacks,
            deprecated=deprecated,
            responses=responses,
            api_version_header_name=api_version_header_name,
        )
        self.swaggers = {}
        router = APIRouter(routes=routes)
        self.docs_url = docs_url
        self.openapi_url = openapi_url

        if self.openapi_url is not None:
            router.add_route(
                path=self.openapi_url,
                endpoint=self.openapi_jsons,
                include_in_schema=False,
            )
            if self.docs_url is not None:
                router.add_route(
                    path=self.docs_url,
                    endpoint=self.swagger_dashboard,
                    include_in_schema=False,
                )
        self.add_unversioned_routers(router)
        self.add_middleware(
            HeaderVersioningMiddleware,
            api_version_header_name=self.router.api_version_header_name,
            api_version_var=self.api_version_var,
            default_response_class=default_response_class,
        )

    def enrich_swagger(self):
        """
        This method goes through all header-based apps and collect a dict[openapi_version, openapi_json]

        For each route a `X-API-VERSION` header with value is added

        """
        unversioned_routes_openapi = get_openapi(
            title=self.title,
            version=self.version,
            openapi_version=self.openapi_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license_info=self.license_info,
            routes=self.router.unversioned_routes,
            tags=self.openapi_tags,
            servers=self.servers,
        )
        if unversioned_routes_openapi["paths"]:
            self.swaggers["unversioned"] = unversioned_routes_openapi

        for header_value, routes in self.router.versioned_routes.items():
            header_value_str = header_value.strftime(VERSION_HEADER_FORMAT)
            openapi = get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
                routes=routes,
                tags=self.openapi_tags,
                servers=self.servers,
            )
            # in current implementation we expect header_value to be a date
            self.swaggers[header_value_str] = openapi

    async def openapi_jsons(self, req: Request) -> JSONResponse:
        version = req.query_params.get("version")
        openapi_of_a_version = self.swaggers.get(version)
        if not openapi_of_a_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OpenApi file of with version `{version}` not found",
            )

        return JSONResponse(openapi_of_a_version)

    async def swagger_dashboard(self, req: Request) -> Response:
        base_url = str(req.base_url).rstrip("/")
        version = req.query_params.get("version")
        if version:
            return get_swagger_ui_html(
                openapi_url=f"{self.openapi_url}?version={version}",
                title="Swagger UI",
            )

        return self.templates.TemplateResponse(
            "docs.html",
            {
                "request": req,
                "table": {version: f"{base_url}{self.docs_url}?version={version}" for version in sorted(self.swaggers)},
            },
        )

    def add_header_versioned_routers(
        self,
        *routers: APIRouter,
        header_value: str,
    ) -> None:
        try:
            header_value_as_dt = datetime.strptime(header_value, VERSION_HEADER_FORMAT).date()
        except ValueError as e:
            raise ValueError(f"header_value should be in `{VERSION_HEADER_FORMAT}` format") from e

        for router in routers:
            added_route_count = len(router.routes)
            self.include_router(
                router,
                dependencies=[Depends(_get_api_version_dependency(self.router.api_version_header_name, header_value))],
            )
            for route in self.routes[len(self.routes) - added_route_count :]:
                self.router.versioned_routes.setdefault(header_value_as_dt, []).append(route)

        self.enrich_swagger()

    def add_unversioned_routers(self, *routers: APIRouter):
        for router in routers:
            self.include_router(router)
            self.router.unversioned_routes.extend(router.routes)
        self.enrich_swagger()

    def add_unversioned_routes(self, *routes: Route):
        self.router.unversioned_routes.extend(routes)
