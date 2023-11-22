import uuid

from fastapi.testclient import TestClient

from fastapi.routing import APIRouter


DEFAULT_API_VERSION = "2021-01-01"
BASIC_HEADERS = {"X-API-VERSION": DEFAULT_API_VERSION}
