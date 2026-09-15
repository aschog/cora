"""The outer test for story 11."""

import datetime
import json
import pathlib

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.file_output import FileOutput
from cora.app.assembly import App
from cora.domain.approval import TOOL
from cora.domain.decision import TurnPaused
from cora.frontends.react.api import api
from cora.plugins.travel import SCOPE
from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME, flat
from cora.plugins.travel.plan import Day, Plan
from cora.plugins.travel.planner import PLAN_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.host import (
    ANSWERING,
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
ANSWER = "Saved it — the three days are on disk now."


DEPART = datetime.date(2026, 9, 7)
SHAPE = json.dumps(
    [
        {"on": "2026-09-07", "doing": ["Fushimi Inari at dawn"]},
        {"on": "2026-09-08", "doing": ["Arashiyama"]},
        {"on": "2026-09-09", "doing": ["Nishiki"]},
    ]
)
PLANNED = Plan(
    origin="BER",
    destination="Kyoto",
    depart=DEPART,
    back=DEPART + datetime.timedelta(days=3),
    days=(
        Day(on=DEPART, doing=("Fushimi Inari at dawn",)),
        Day(on=DEPART + datetime.timedelta(days=1), doing=("Arashiyama",)),
        Day(on=DEPART + datetime.timedelta(days=2), doing=("Nishiki",)),
    ),
)
ITINERARY = "Fushimi Inari at dawn"


def _planning() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=PLAN_TOOL_NAME,
                arguments={
                    "origin": "BER",
                    "destination": "Kyoto",
                    "window_start": DEPART.isoformat(),
                    "window_end": (DEPART + datetime.timedelta(days=3)).isoformat(),
                    "nights": 3,
                },
                call_id="p1",
            ),
        )
    )


def _saving() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=ITINERARY_TOOL_NAME,
                arguments={"title": TITLE, **flat(PLANNED)},
                call_id="s1",
            ),
        )
    )


def _plans_then_saves(answer: str) -> ScriptedChatModel:
    return ScriptedChatModel(
        [_planning(), SHAPE_REPLY, _saving(), ModelReply(text=answer)]
    )


SHAPE_REPLY = ModelReply(text=SHAPE)


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
    model = _plans_then_saves(ANSWER)
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
    assert read[TOOL] == ITINERARY_TOOL_NAME
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


def test_a_plugin_that_takes_part_everywhere_it_may_cannot_switch_the_gate_off(
    tmp_path: pathlib.Path,
) -> None:
    """The gate is a step of the core, not a point a plugin subscribes to: a plugin can
    refuse a call or amend a result, and there is nothing it can return that lets one
    through unasked — because nothing a handler returns can pause a turn either."""
    everywhere = Extension(module="fixture_plugins.everywhere", extend=_taking_part)
    model = _plans_then_saves(ANSWER)
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
    for event in (SCREENING, BRIEFING, CALLING, RETURNING, ANSWERING):
        cora.register_handler(event=event, handle=lambda *_, **__: None)
