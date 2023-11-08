from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.dependencies.utils import get_body_field, get_dependant, get_parameterless_sub_dependant
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute, APIRouter
from fastapi.templating import Jinja2Templates
from starlette.routing import Route

from .assembly.responses import responses
from .configs import X_MONITE_VERSION_HEADER_VALUE_FORMAT
from .dependencies.versioning import get_predefined_monite_version_header
from .exceptions import MoniteAppCreationError
from .routing import MoniteAPIRouter, RootHeaderAPIRouter
from .utils import StrThatYouCantConcatenate, get_schema_duplication_error_message

CURR_DIR = Path(__file__).resolve()
logger = getLogger(__name__)


class HeaderRoutingFastAPI(FastAPI):
    templates = Jinja2Templates(directory=CURR_DIR.parent / "docs")

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["docs_url"] = None
        kwargs["redoc_url"] = None
        if "routes" in kwargs:
            raise MoniteAppCreationError(
                "Please use `add_header_versioned_routers` or `add_unversioned_routers`",
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

    def enrich_swagger(self):
        """
        This method goes through all header-based apps and collect a dict[openapi_version, openapi_json]

        For each route a `x-monite-version` header with value is added

        If there are any duplicated schema names, located in different modules, it will fail with
        SchemaDuplicationError in order to prevent weird
        schema names like `api__v1___shared__pagination_depends__OrderEnum`
        """
        self.swaggers["unversioned"] = get_openapi(
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
        for header_value, routes in self.router.versioned_routes.items():
            header_value_str = header_value.strftime(X_MONITE_VERSION_HEADER_VALUE_FORMAT)
            for route in routes:
                if not isinstance(route, APIRoute):
                    continue
                route.dependencies.append(Depends(get_predefined_monite_version_header(header_value)))
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

        for openapi in self.swaggers.values():
            duplicates = {}
            for model_name in openapi.get("components", {}).get("schemas", []):
                splitted_model_name = model_name.split("__")
                if len(splitted_model_name) > 1:
                    # then splitted_model_name is `api__v1___shared__pagination_depends__OrderEnum`
                    original_model_name = splitted_model_name[-1]
                    model_path = ".".join(splitted_model_name[:-1])
                    duplicates.setdefault(original_model_name, []).append(model_path)
            if duplicates:
                error_msg = get_schema_duplication_error_message(duplicates)
                logger.warning(error_msg, stacklevel=4)

    async def openapi_jsons(self, req: Request):
        version = req.query_params.get("version")
        openapi_of_a_version = self.swaggers.get(version)
        if not openapi_of_a_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OpenApi file of with version `{version}` not found",
            )

        return JSONResponse(openapi_of_a_version)

    async def swagger_dashboard(self, req: Request):
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
        *routers: MoniteAPIRouter,
        header_value: str,
    ) -> None:
        try:
            header_value_as_dt = datetime.strptime(
                header_value,
                X_MONITE_VERSION_HEADER_VALUE_FORMAT,
            ).date()
        except ValueError as e:
            raise ValueError(
                f"header_value should be in `{X_MONITE_VERSION_HEADER_VALUE_FORMAT}` format",
            ) from e

        for router in routers:
            last_routes = len(router.routes)
            self.include_router(router)
            for route in self.routes[-last_routes:]:
                if isinstance(route, APIRoute):
                    _rename_file_schemas(route)
                    if not route.responses:
                        route.responses = responses
                self.router.versioned_routes.setdefault(
                    header_value_as_dt,
                    [],
                ).append(route)

        self.enrich_swagger()

    def add_unversioned_routers(self, *routers: APIRouter):
        for router in routers:
            self.include_router(router)
            self.router.unversioned_routes.extend(router.routes)
        self.enrich_swagger()

    def add_unversioned_routes(self, *routes: Route):
        self.router.unversioned_routes.extend(routes)

    def add_webhook_routers(self, *routers: MoniteAPIRouter) -> None:
        self.add_unversioned_routers(*routers)


def _rename_file_schemas(route: APIRoute):
    body_field = get_body_field(dependant=route.dependant, name=route.unique_id)
    if body_field and body_field.name == "body":
        if route.openapi_extra and route.openapi_extra.get("schema_name"):
            schema_name = route.openapi_extra.pop("schema_name")
        else:
            raise MoniteAppCreationError(
                f"There is a `File` or `UploadFile` field in the route with `{route.name=}` "
                f"and `{route.path=}` and no custom `schema_name` provided. "
                'Please pass `openapi_extra={"schema_name": "SCHEMA_NAME_HERE"}`',
            )
        # then we need to regenerate with the fancy name
        body_field = get_body_field(dependant=route.dependant, name=StrThatYouCantConcatenate(schema_name))

    route.body_field = body_field
