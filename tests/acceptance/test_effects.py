"""The outer test for story 11."""

import pathlib

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.file_output import FileOutput
from cora.app.assembly import App
from cora.domain.decision import TurnPaused
from cora.engine.steps import DECLINED_CALL
from cora.frontends.react.api import api
from cora.plugins.travel import SCOPE
from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.host import (
    BRIEFING,
    CALLING,
    RETURNING,
    SCREENING,
    Extension,
    Host,
)
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


def _travel() -> Extension:
    from cora.plugins.travel import extend

    return Extension(module="cora.plugins.travel", extend=extend)


def _app(model: ScriptedChatModel, output: pathlib.Path) -> App:
    return assembled(
        chat_model=model,
        plugins=(_travel(),),
        scopes=(SCOPE,),
        output=FileOutput.at(str(output)),
    )


def _of(body: str, name: str) -> list[dict]:
    return [data for event, data in frames(body) if event == name]


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
            "/api/resume", json={"thread_id": THREAD, "answer": "s1"}
        )

    card = proposed["card"]
    read = {field["name"]: field["value"] for field in card["fields"]}
    assert read["tool"] == ITINERARY_TOOL_NAME
    assert card["prompt"], "the card says what the call would do"
    assert read["title"] == TITLE
    assert not any(field["editable"] for field in card["fields"])
    assert not _of(asked.text, "turn"), "a proposed effect is not an answered turn"
    assert waiting["card"]["actions"][0]["answer"] == "s1"
    assert before == [], "nothing outside cora changed while the turn waited"

    [turn] = _of(approved.text, "turn")
    assert turn["answer"] == ANSWER
    [written] = [path for path in output.rglob("*") if path.is_file()]
    assert ITINERARY in written.read_text()
    assert any(
        "approved" in step["summary"].lower() and ITINERARY_TOOL_NAME in step["summary"]
        for step in turn["trace"]
    ), "the approval is on the trace, beside the call it authorised"


DECLINED_QUESTION = "Save the Kyoto days."


def test_declining_changes_nothing_and_the_model_is_told_it_did_not_happen(
    tmp_path: pathlib.Path,
) -> None:
    """The other side of the story: a no leaves everything outside cora as it was, the
    call never runs, and the turn is still answered — with the model told plainly that
    the thing it asked for did not happen, so it can say so."""
    output = tmp_path / "output"
    model = ScriptedChatModel([_saving(), ModelReply(text="I have not saved it.")])
    with TestClient(api(_app(model, output))) as reader:
        reader.post(
            "/api/ask", json={"question": DECLINED_QUESTION, "thread_id": THREAD}
        )
        declined = reader.post(
            "/api/resume", json={"thread_id": THREAD, "answer": None}
        )

    [turn] = _of(declined.text, "turn")
    assert turn["answer"] == "I have not saved it."
    assert not output.exists(), "nothing outside cora changed"
    told = [message.content for message in model.last_messages or ()]
    assert DECLINED_CALL.format(name=ITINERARY_TOOL_NAME) in told


def test_a_plugin_that_takes_part_everywhere_it_may_cannot_switch_the_gate_off(
    tmp_path: pathlib.Path,
) -> None:
    """The gate is a step of the core, not a point a plugin subscribes to: a plugin can
    refuse a call or amend a result, and there is nothing it can return that lets one
    through unasked — because nothing a handler returns can pause a turn either."""
    everywhere = Extension(module="fixture_plugins.everywhere", extend=_taking_part)
    model = ScriptedChatModel([_saving(), ModelReply(text=ANSWER)])
    app = assembled(
        chat_model=model,
        plugins=(_travel(), everywhere),
        scopes=(SCOPE,),
        output=FileOutput.at(str(tmp_path / "output")),
    )

    with pytest.raises(TurnPaused) as stopped:
        app.agent.answer(QUESTION, THREAD)

    card = stopped.value.pending.card
    assert ITINERARY_TOOL_NAME in [field.value for field in card.fields]
    assert list((tmp_path / "output").rglob("*")) == []


def _taking_part(cora: Host) -> None:
    """One plugin at every point in a turn it is allowed to be at, each handler letting
    everything through — which is the most a plugin can do about a call.

    Every one of them answers with nothing, which is what "no objection, no amendment"
    is: a refusing event reads anything at all as a refusal, and an amending one reads
    nothing as leaving the value alone.
    """
    for event in (SCREENING, BRIEFING, CALLING, RETURNING):
        cora.register_handler(event=event, handle=lambda *_, **__: None)
