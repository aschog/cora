"""The outer test for the story: the coach lists every workout the trainer logged by
day and by name, gives the numbers only when asked, and shows the plan as neither."""

import pytest
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
# Posted as the trainer posts them: named for the day, a heading per exercise with its
# load and one set line. The day saved twice is a wrist save and a page save.
POSTED = [
    ("2026-09-18.md", "# Deadlift, conventional 14 kg\n3 sets of 10\n"),
    ("2026-09-16.md", "# Swing 16 kg\n2 sets of 10\n"),
    ("2026-09-18.md", "# Snatch 14 kg\nsets of 8 / 8\n"),
    ("training-plan.md", "# 4-Week Beginner Strength Plan\n\nThree sessions a week.\n"),
]
ANSWER = "Two days logged: swings on the 16th, then deadlift and snatch on the 18th."
BY_NAME = "2026-09-16: Swing\n2026-09-18: Deadlift, conventional · Snatch"
IN_DETAIL = """\
2026-09-16
- Swing — 16 kg · 2x10 · 20 reps · 320 kg

2026-09-18
- Deadlift, conventional — 14 kg · 3x10 · 30 reps · 420 kg
- Snatch — 14 kg · 8+8 · 16 reps · 224 kg"""


@pytest.mark.xfail(strict=True, reason="the tool answers in numbers, not in text")
def test_the_coach_names_the_workouts_and_gives_the_numbers_on_request() -> None:
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
                ModelReply(text=ANSWER),
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
                    "question": "Show me all my trainings",
                    "thread_id": "t1",
                    "pin": FITNESS,
                },
            ).text
        )

    turn = streamed[-1][1]
    assert turn["answer"] == ANSWER
    by_name, in_detail = [
        step for step in turn["trace"] if step["summary"].startswith(f"{TOOL_NAME}(")
    ]
    assert not by_name["failed"], by_name["detail"]
    assert by_name["detail"] == BY_NAME
    assert not in_detail["failed"], in_detail["detail"]
    assert in_detail["detail"] == IN_DETAIL
