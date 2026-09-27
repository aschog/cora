import asyncio
import json
import threading
from collections.abc import Callable
from typing import Any

from cora.frontends.react.api import TURN_THREAD
from sse import frames

Frames = list[tuple[str, dict]]


# The thread walking the one turn in flight, so a test can wait for it to end.
def turn_thread() -> threading.Thread:
    walking = [each for each in threading.enumerate() if each.name == TURN_THREAD]
    assert len(walking) == 1
    return walking[0]


# Drives an ASGI app the way a server does, and goes away at the frame `until` names —
# which `TestClient` cannot do, reading a response whole before it hands one back.
def driven(
    app: Any, path: str, asked: dict[str, Any], *, until: Callable[[str], bool]
) -> Frames:
    return asyncio.run(_drive(app, path, asked, until))


async def _drive(
    app: Any, path: str, asked: dict[str, Any], until: Callable[[str], bool]
) -> Frames:
    body = json.dumps(asked).encode()
    gone = asyncio.Event()
    read: list[str] = []
    posted = False

    async def receive() -> dict[str, Any]:
        nonlocal posted
        if not posted:
            posted = True
            return {"type": "http.request", "body": body, "more_body": False}
        await gone.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message["type"] != "http.response.body":
            return
        read.append(message.get("body", b"").decode())
        if until("".join(read)):
            gone.set()

    await app(_posting(path, len(body)), receive, send)
    return frames("".join(read))


def _posting(path: str, length: int) -> dict[str, Any]:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(length).encode()),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
