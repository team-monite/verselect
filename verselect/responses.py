from typing import Any

from fastapi.responses import ORJSONResponse
from monite_common.serializers import orjson_dumps_to_bytes
from pydantic import BaseModel


class ErrorSchema(BaseModel):
    message: str


class ErrorSchemaResponse(BaseModel):
    error: ErrorSchema


class CustomORJSONResponse(ORJSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson_dumps_to_bytes(content)
