import pathlib

import pytest
from starlette.testclient import TestClient

from cora.app.config import Config
from cora.frontends.react.api import api

PACKAGE_INIT = """\
from cora.ports.host import Host

from .notes import INSTRUCTIONS


def extend(cora: Host) -> None:
    cora.register_instructions(INSTRUCTIONS, scope="interview")
"""

NOTES = 'INSTRUCTIONS = "Answer as an interviewer."\n'


def _config(root: pathlib.Path, folder: pathlib.Path) -> Config:
    return Config(
        api_key="k",
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        plugin_modules=(),
        top_k=3,
        max_tool_rounds=4,
        history_turns=6,
        max_output_tokens=1024,
        request_timeout_seconds=30,
        reasoning_effort="low",
        db_path=str(root / "db"),
        memory_path=str(root / "memory.sqlite"),
        documents_path=str(root / "documents"),
        conversations_path=str(root / "conversations.sqlite"),
        log_path=str(root / "logs" / "cora.log"),
        plugins_path=str(folder),
        debug=False,
    )


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
    from app_builder import assembled
    from cora.app.assembly import LiveApp

    holder = LiveApp(
        named=(),
        folder=tmp_path,
        compose=lambda loaded, dropped: assembled(plugins=loaded, scopes_from=dropped),
    )
    reader = TestClient(api(holder))
    assert reader.get("/api/scopes").json()["available"] == []
    assert reader.get("/api/documents?scope=birds").status_code == 400

    (tmp_path / "field_notes.py").write_text(INSTRUCTIONS_ONLY)

    assert reader.get("/api/scopes").json()["available"] == ["birds"]
    listed = reader.get("/api/documents?scope=birds")
    assert listed.status_code == 200 and listed.json() == []

    (tmp_path / "field_notes.py").unlink()
    assert reader.get("/api/scopes").json()["available"] == []


def test_the_api_reads_the_current_composition_per_request(
    tmp_path: pathlib.Path,
) -> None:
    """The api holds the folder's holder, not one boot-time app: what a page reload
    shows is whatever the folder holds by then, and a broken drop is a readable
    refusal rather than a dead deployment."""
    from app_builder import assembled
    from cora.app.assembly import LiveApp

    holder = LiveApp(
        named=(),
        folder=tmp_path,
        compose=lambda loaded, dropped: assembled(plugins=loaded),
    )
    reader = TestClient(api(holder))
    assert reader.get("/api/plugins").json() == []

    (tmp_path / "field_notes.py").write_text(INSTRUCTIONS_ONLY)
    listed = reader.get("/api/plugins").json()
    assert [each["name"] for each in listed] == ["field_notes"]

    (tmp_path / "broken.py").write_text("raise RuntimeError('boom')\n")
    refused = reader.get("/api/plugins")
    assert refused.status_code == 400
    assert "broken" in refused.json()["error"]

    (tmp_path / "broken.py").unlink()
    assert [each["name"] for each in reader.get("/api/plugins").json()] == [
        "field_notes"
    ]


@pytest.mark.integration
def test_a_package_dropped_while_serving_answers_the_next_listing_read(
    tmp_path: pathlib.Path,
) -> None:
    """The whole story at once: a folder of plain `.py` files, a relative import
    inside it, dropped while the process serves — and the next read has it."""
    from cora.app.assembly import live

    folder = tmp_path / "plugins"
    folder.mkdir()
    reader = TestClient(api(live(_config(tmp_path, folder))))
    assert reader.get("/api/plugins").json() == []

    package = folder / "interview"
    package.mkdir()
    (package / "notes.py").write_text(NOTES)
    (package / "__init__.py").write_text(PACKAGE_INIT)

    listed = reader.get("/api/plugins").json()
    assert [each["name"] for each in listed] == ["interview"]
    assert listed[0]["source"] == str(package)
    assert reader.get("/api/scopes").json()["available"] == ["interview"]
