"""The outer test for the story: the coach lists every workout the trainer logged, one
session per day with its numbers, and the plan beside them is not one."""

import json
from typing import Any

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


def test_the_coach_lists_the_workouts_by_day_with_their_numbers() -> None:
    app = assembled(
        plugins=(load_plugin("cora.plugins.fitness"),),
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    text="",
                    tool_calls=(
                        ToolCall(name=TOOL_NAME, arguments={}, call_id="call-1"),
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
    [listed] = [
        step for step in turn["trace"] if step["summary"].startswith(f"{TOOL_NAME}(")
    ]
    assert not listed["failed"], listed["detail"]
    sessions: list[dict[str, Any]] = json.loads(listed["detail"])
    assert [session["date"] for session in sessions] == ["2026-09-16", "2026-09-18"]
    swing, (deadlift, snatch) = sessions[0]["movements"], sessions[1]["movements"]
    assert [(m["name"], m["load"], m["reps"], m["volume_kg"]) for m in swing] == [
        ("Swing", "16 kg", 20, 320)
    ]
    assert (deadlift["name"], deadlift["sets"], deadlift["reps"]) == (
        "Deadlift, conventional",
        [10, 10, 10],
        30,
    )
    assert (snatch["name"], snatch["sets"], snatch["volume_kg"]) == (
        "Snatch",
        [8, 8],
        224,
    )
