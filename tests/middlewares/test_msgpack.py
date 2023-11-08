import re
from collections.abc import Sized
from typing import cast

import httpx
import msgpack
import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.types import Message, Receive, Scope, Send

from verselect.middlewares.msgpack import MessagePackMiddleware

# copy-paste from https://github.com/florimondmanca/msgpack-asgi


async def mock_receive() -> Message:
    raise NotImplementedError


async def mock_send(message: Message) -> None:
    raise NotImplementedError


async def test__msgpack_request() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive)
        content_type = request.headers["content-type"]
        data = await request.json()
        message = data["message"]
        text = f"content_type={content_type!r} message={message!r}"

        response = PlainTextResponse(text)
        await response(scope, receive, send)

    app = MessagePackMiddleware(app)

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        content = {"message": "Hello, world!"}
        body = msgpack.packb(content)
        r = await client.post("/", content=body, headers={"content-type": "application/x-msgpack"})
        assert r.status_code == 200
        assert r.text == "content_type='application/json' message='Hello, world!'"


async def test__non_msgpack_request() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive)
        content_type = request.headers["content-type"]
        message = (await request.body()).decode()
        text = f"content_type={content_type!r} message={message!r}"

        response = PlainTextResponse(text)
        await response(scope, receive, send)

    app = MessagePackMiddleware(app)

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        r = await client.post(
            "/",
            content="Hello, world!",
            headers={"content-type": "text/plain"},
        )
        assert r.status_code == 200
        assert r.text == "content_type='text/plain' message='Hello, world!'"


async def test__msgpack_accepted() -> None:
    app = MessagePackMiddleware(JSONResponse({"message": "Hello, world!"}))

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        r = await client.get("/", headers={"accept": "application/x-msgpack"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/x-msgpack"
        expected_data = {"message": "Hello, world!"}
        assert int(r.headers["content-length"]) == len(cast(Sized, msgpack.packb(expected_data)))
        assert msgpack.unpackb(r.content, raw=False) == expected_data


async def test__msgpack_accepted_but_response_is_not_json() -> None:
    app = MessagePackMiddleware(PlainTextResponse("Hello, world!"))

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        r = await client.get("/", headers={"accept": "application/x-msgpack"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/plain; charset=utf-8"
        assert r.text == "Hello, world!"


async def test__msgpack_accepted_and_response_is_already_msgpack() -> None:
    data = msgpack.packb({"message": "Hello, world!"})
    response = Response(data, media_type="application/x-msgpack")
    app = MessagePackMiddleware(response)

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        r = await client.get("/", headers={"accept": "application/x-msgpack"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/x-msgpack"
        expected_data = {"message": "Hello, world!"}

        assert int(r.headers["content-length"]) == len(cast(Sized, msgpack.packb(expected_data)))
        assert msgpack.unpackb(r.content, raw=False) == expected_data


async def test__msgpack_not_accepted() -> None:
    app = MessagePackMiddleware(JSONResponse({"message": "Hello, world!"}))

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        r = await client.get("/")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"
        assert r.json() == {"message": "Hello, world!"}
        with pytest.raises(ValueError, match=re.escape("unpack(b) received extra data.")):
            msgpack.unpackb(r.content)


async def test__request_is_not_http() -> None:
    async def lifespan_only_app(scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "lifespan"

    app = MessagePackMiddleware(lifespan_only_app)
    scope = {"type": "lifespan"}
    await app(scope, mock_receive, mock_send)


async def test__packb_unpackb() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        assert await request.json() == {"message": "unpacked"}

        response = JSONResponse({"message": "Hello, World!"})
        await response(scope, receive, send)

    app = MessagePackMiddleware(
        app,
        packb=lambda *a: b"packed",
        unpackb=lambda *a: {"message": "unpacked"},
    )

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        r = await client.post(
            "/",
            content="Hello, World",
            headers={
                "content-type": "application/x-msgpack",
                "accept": "application/x-msgpack",
            },
        )
        assert r.text == "packed"
