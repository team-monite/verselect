from fastapi import Response
from starlette.responses import PlainTextResponse


async def basic_ping_endpoint() -> PlainTextResponse:
    return PlainTextResponse("pong")


async def healthz_endpoint() -> Response:
    return Response(b'{"temperature": 36.6}')
