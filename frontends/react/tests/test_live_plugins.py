import asyncio
import pathlib
import time

import httpx
import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import LiveApp
from cora.frontends.react.api import api

INSTRUCTIONS_ONLY = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""


def test_a_dropped_field_is_offered_and_the_rails_follow_it(
    tmp_path: pathlib.Path,
) -> None:
    """The field arrives with the plugin: the picker's list, the documents rail and
    the pin all read the composition the folder describes, not a startup setting."""
    holder = LiveApp(
        named=(),
        folder=tmp_path,
        compose=lambda loaded: assembled(plugins=loaded),
    )
    reader = TestClient(api(holder))
    assert reader.get("/api/scopes").json()["available"] == []
    assert reader.get("/api/documents?scope=birds").status_code == 400

    (tmp_path / "field_notes.py").write_text(INSTRUCTIONS_ONLY)

    assert reader.get("/api/scopes").json()["available"] == ["birds"]
    added = reader.post(
        "/api/documents",
        files={"file": ("sightings.md", b"Twelve waders at dawn.", "text/markdown")},
        data={"scope": "birds"},
    )
    assert added.status_code == 200 and added.json()["scope"] == "birds"
    assert reader.get("/api/documents?scope=birds").json() == ["sightings.md"]

    (tmp_path / "field_notes.py").unlink()
    assert reader.get("/api/scopes").json()["available"] == []


SLOW_IMPORT = f"import time\ntime.sleep(0.8)\n{INSTRUCTIONS_ONLY}"


@pytest.mark.integration
def test_a_slow_drop_does_not_stall_the_event_loop(tmp_path: pathlib.Path) -> None:
    """Recomposing runs plugin imports, and an async handler that pays for that on the
    event loop stalls every stream and request on the page. The 404 below touches no
    composition, so it answers immediately — unless the loop itself is held."""
    holder = LiveApp(
        named=(),
        folder=tmp_path,
        compose=lambda loaded: assembled(plugins=loaded),
    )
    served = api(holder)

    async def race() -> tuple[int, float, int]:
        transport = httpx.ASGITransport(app=served)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            (tmp_path / "slow.py").write_text(SLOW_IMPORT)
            asking = asyncio.create_task(
                c.post("/api/ask", json={"question": "hi", "thread_id": "t1"})
            )
            # The clock starts before yielding: a held loop stalls this coroutine
            # itself, so stamping after the yield would hide exactly the stall.
            started = time.monotonic()
            await asyncio.sleep(0.05)
            pong = await c.get("/api/nothing")
            elapsed = time.monotonic() - started
            asked = await asking
            return pong.status_code, elapsed, asked.status_code

    status, elapsed, asked = asyncio.run(race())

    assert status == 404
    assert asked == 200
    assert elapsed < 0.4, "the event loop was held for the length of a plugin import"
