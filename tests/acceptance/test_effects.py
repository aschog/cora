"""The outer test for story 11."""

import pathlib

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.file_output import FileOutput
from cora.app.assembly import App
from cora.frontends.react.api import api
from cora.plugins.travel import SCOPE
from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from sse import frames

THREAD = "the-trip-i-approve-of"
QUESTION = "Save the three days in Kyoto we worked out."
TITLE = "kyoto-three-days"
ITINERARY = "Day 1 — Fushimi Inari at dawn.\nDay 2 — Arashiyama.\nDay 3 — Nishiki."
ANSWER = "Saved it — the three days are on disk now."


def _saving() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=ITINERARY_TOOL_NAME,
                arguments={"title": TITLE, "itinerary": ITINERARY},
                call_id="s1",
            ),
        )
    )


def _app(model: ScriptedChatModel, output: pathlib.Path) -> App:
    from cora.plugins.travel import extend

    return assembled(
        chat_model=model,
        plugins=(Extension(module="cora.plugins.travel", extend=extend),),
        scopes=(SCOPE,),
        output=FileOutput.at(str(output)),
    )


def _of(body: str, name: str) -> list[dict]:
    return [data for event, data in frames(body) if event == name]


@pytest.mark.xfail(strict=True, reason="story 11 is in flight")
def test_an_effect_happens_only_after_i_approve_it(tmp_path: pathlib.Path) -> None:
    """The criterion: cora says what it is about to do, nothing outside it changes while
    the turn waits, and the approval is on the trace beside the call it authorised."""
    output = tmp_path / "output"
    model = ScriptedChatModel([_saving(), ModelReply(text=ANSWER)])
    with TestClient(api(_app(model, output))) as reader:
        asked = reader.post(
            "/api/ask", json={"question": QUESTION, "thread_id": THREAD}
        )
        [proposed] = _of(asked.text, "paused")
        waiting = reader.get(f"/api/sessions/{THREAD}/pending").json()
        before = sorted(path.name for path in output.rglob("*") if path.is_file())
        approved = reader.post(
            "/api/approve",
            json={"thread_id": THREAD, "call_id": "s1", "approved": True},
        )

    proposal = proposed["proposal"]
    assert proposal["tool"] == ITINERARY_TOOL_NAME
    assert proposal["does"], "the card says what the call would do"
    assert proposal["arguments"]["title"] == TITLE
    assert not _of(asked.text, "turn"), "a proposed effect is not an answered turn"
    assert waiting["proposal"]["call_id"] == "s1"
    assert waiting["decision"] is None, "it stopped on a proposal, not on a decision"
    assert before == [], "nothing outside cora changed while the turn waited"

    [turn] = _of(approved.text, "turn")
    assert turn["answer"] == ANSWER
    [written] = [path for path in output.rglob("*") if path.is_file()]
    assert ITINERARY in written.read_text()
    assert any(
        "approved" in step["summary"].lower() and ITINERARY_TOOL_NAME in step["summary"]
        for step in turn["trace"]
    ), "the approval is on the trace, beside the call it authorised"
