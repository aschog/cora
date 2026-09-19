"""The outer test for the story: a save carries the name of the workout it was, and the
coach names a day by its workouts rather than by their lifts."""

from starlette.testclient import TestClient

from app_builder import assembled
from cora.engine.plugin_registry import load_plugin
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, ScriptedChatModel
from sse import frames

FITNESS = "fitness"
TOOL_NAME = "list_workouts"
# The sheet's tab and one of its exercises, in the language the sheet is written in.
SNATCH_WORKOUT = "Рывок гири"
ONE_ARM_SWING = "Мах одной рукой"  # noqa: RUF001
# A save from the sheet, titled, and an earlier one from the embedded plan, untitled.
POSTED = [
    (
        "2026-09-18-16-20-05.md",
        f"{SNATCH_WORKOUT}\n\n# {ONE_ARM_SWING} 14 kg\n2 sets of 10\n",
    ),
    ("2026-09-18-12-27-00.md", "# Deadlift, conventional 14 kg\n3 sets of 10\n"),
]
BY_NAME = (
    f"2026-09-18: {SNATCH_WORKOUT} · untitled save: Deadlift, conventional\n"
    "1 day, 2 saves. The sets, reps and weights are in the details."
)
IN_DETAIL = (
    f"2026-09-18 — {SNATCH_WORKOUT}\n"
    "- Deadlift, conventional — 14 kg · 3x10 · 30 reps · 420 kg\n"
    f"- {ONE_ARM_SWING} — 14 kg · 2x10 · 20 reps · 280 kg"
)


def test_the_coach_names_a_day_by_its_workouts() -> None:
    app = assembled(
        plugins=(load_plugin("cora.plugins.fitness"),),
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    text="",
                    tool_calls=(
                        ToolCall(name=TOOL_NAME, arguments={}, call_id="call-1"),
                        ToolCall(
                            name=TOOL_NAME, arguments={"detail": True}, call_id="call-2"
                        ),
                    ),
                ),
                ModelReply(text="Listed."),
            ]
        ),
        conversations=FakeConversations(),
    )

    with TestClient(api(app)) as reader:
        for name, text in POSTED:
            added = reader.post(
                "/api/documents",
                files={"file": (name, text.encode(), "text/markdown")},
                data={"scope": FITNESS},
            )
            assert added.status_code == 200, added.text
        streamed = frames(
            reader.post(
                "/api/ask",
                json={
                    "question": "What did I train?",
                    "thread_id": "t1",
                    "pin": FITNESS,
                },
            ).text
        )

    by_name, in_detail = [
        step
        for step in streamed[-1][1]["trace"]
        if step["summary"].startswith(f"{TOOL_NAME}(")
    ]
    assert by_name["detail"] == BY_NAME
    assert in_detail["detail"] == IN_DETAIL
