from contextvars import ContextVar
from datetime import date, datetime
from logging import getLogger
from pathlib import Path
from typing import Any, cast

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.dependencies.utils import get_dependant, get_parameterless_sub_dependant
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute, APIRouter
from fastapi.templating import Jinja2Templates
from starlette.routing import Route

from verselect.routing import VERSION_HEADER_FORMAT

from .exceptions import VerselectAppCreationError
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
        routes: None = None,
        **kwargs: Any,
    ):
        if api_version_var is None:
            api_version_var = ContextVar("api_header_version")
        self.api_version_var = api_version_var
        kwargs["docs_url"] = None
        kwargs["redoc_url"] = None
        if routes:
            raise VerselectAppCreationError(
                f"It's prohibited to pass routes to {HeaderRoutingFastAPI.__name__}. "
                f"Please use `{self.add_header_versioned_routers.__name__}` "
                f"or `{self.add_unversioned_routers.__name__}`",
            )
        super().__init__(*args, **kwargs)
        self.router: RootHeaderAPIRouter = RootHeaderAPIRouter(
            routes=self.routes,
            on_startup=kwargs.get("on_startup"),
            on_shutdown=kwargs.get("on_shutdown"),
            default_response_class=kwargs.get("default_response_class", JSONResponse),
            dependencies=kwargs.get("dependencies"),
            callbacks=kwargs.get("callbacks"),
            deprecated=kwargs.get("deprecated"),
            include_in_schema=kwargs.get("include_in_schema", True),
            responses=kwargs.get("responses"),
            api_version_header_name=api_version_header_name,
        )
        self.swaggers = {}
        router = APIRouter()
        router.add_route(
            path="/docs",
            endpoint=self.swagger_dashboard,
            include_in_schema=False,
        )
        router.add_route(
            path="/openapi.json",
            endpoint=self.openapi_jsons,
            include_in_schema=False,
        )
        self.add_unversioned_routers(router)

        def middleware(*a: Any, **kw: Any) -> HeaderVersioningMiddleware:
            return HeaderVersioningMiddleware(
                *a,
                api_version_header_name=self.router.api_version_header_name,
                api_version_var=self.api_version_var,
                **kw,
            )

        self.add_middleware(cast(Any, middleware))

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
            for route in routes:
                if not isinstance(route, APIRoute):
                    continue
                route.dependencies.append(
                    Depends(_get_api_version_dependency(self.router.api_version_header_name, header_value)),
                )
                route.dependant = get_dependant(path=route.path_format, call=route.endpoint)
                for depends in route.dependencies[::-1]:
                    route.dependant.dependencies.insert(
                        0,
                        get_parameterless_sub_dependant(depends=depends, path=route.path_format),
                    )

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
                openapi_url=f"/openapi.json?version={version}",
                title="Swagger UI",
            )

        return self.templates.TemplateResponse(
            "docs.html",
            {
                "request": req,
                "table": {version: f"{base_url}/docs?version={version}" for version in sorted(self.swaggers)},
            },
        )

    def add_header_versioned_routers(
        self,
        *routers: APIRouter,
        header_value: str,
    ) -> None:
        try:
            header_value_as_dt = datetime.strptime(
                header_value,
                VERSION_HEADER_FORMAT,
            ).date()
        except ValueError as e:
            raise ValueError(f"header_value should be in `{VERSION_HEADER_FORMAT}` format") from e

        for router in routers:
            last_routes = len(router.routes)
            self.include_router(router)
            for route in self.routes[-last_routes:]:
                self.router.versioned_routes.setdefault(header_value_as_dt, []).append(route)

        self.enrich_swagger()

    def add_unversioned_routers(self, *routers: APIRouter):
        for router in routers:
            self.include_router(router)
            self.router.unversioned_routes.extend(router.routes)
        self.enrich_swagger()

    def add_unversioned_routes(self, *routes: Route):
        self.router.unversioned_routes.extend(routes)
