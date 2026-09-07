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


@pytest.mark.integration
@pytest.mark.xfail(strict=True, reason="dropped-plugin-packages is in flight")
def test_a_package_dropped_while_serving_answers_the_next_listing_read(
    tmp_path: pathlib.Path,
) -> None:
    """The whole story at once: a folder of plain `.py` files, a relative import
    inside it, dropped while the process serves — and the next read has it."""
    from cora.app import assembly

    live = getattr(assembly, "live")  # noqa: B009 — not there until the slice lands

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
