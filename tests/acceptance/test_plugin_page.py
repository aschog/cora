import pathlib

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import LiveApp
from cora.frontends.react.api import api

TRAINER = """\
import pathlib

from cora.ports.host import Host

SCOPE = "training"


def extend(cora: Host) -> None:
    cora.register_instructions("You coach lifting.", scope=SCOPE)
    cora.register_page(pathlib.Path(__file__).parent / "page", scope=SCOPE)
"""

ENTRY = "<!doctype html><title>Trainer</title><p>one screen"


def test_a_dropped_plugin_brings_a_page_and_takes_it_away_again(
    tmp_path: pathlib.Path,
) -> None:
    holder = LiveApp(
        named=(), folder=tmp_path, compose=lambda loaded: assembled(plugins=loaded)
    )
    reader = TestClient(api(holder))
    assert reader.get("/api/scopes").json()["pages"] == {}

    trainer = tmp_path / "trainer"
    (trainer / "page").mkdir(parents=True)
    (trainer / "__init__.py").write_text(TRAINER)
    (trainer / "page" / "index.html").write_text(ENTRY)

    where = reader.get("/api/scopes").json()["pages"]["training"]
    served = reader.get(where)
    assert served.status_code == 200
    assert ENTRY in served.text

    (trainer / "__init__.py").unlink()
    (trainer / "page" / "index.html").unlink()
    (trainer / "page").rmdir()
    trainer.rmdir()

    assert reader.get("/api/scopes").json()["pages"] == {}
    assert reader.get(where).status_code == 404
