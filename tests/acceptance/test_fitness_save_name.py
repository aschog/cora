"""The outer test for the story: a save is named for its moment, and a day's saves
list in the order they happened whatever order they reached cora in."""

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
# Named as the trainer names them now, the later save posted first.
POSTED = [
    ("2026-09-18-16-42-10.md", "# Snatch 14 kg\nsets of 8 / 8\n"),
    ("2026-09-18-16-20-05.md", "# Deadlift, conventional 14 kg\n3 sets of 10\n"),
]
BY_NAME = (
    "2026-09-18: untitled save: Deadlift, conventional · untitled save: Snatch\n"
    "1 day, 2 saves. The sets, reps and weights are in the details."
)
IN_DETAIL = """\
2026-09-18
- Deadlift, conventional — 14 kg · 3x10 · 30 reps · 420 kg
- Snatch — 14 kg · 2x8 · 16 reps · 224 kg"""


def test_a_days_saves_list_in_the_order_they_happened() -> None:
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
        listed = reader.get(f"/api/documents?scope={FITNESS}").json()
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

    assert listed == [name for name, _ in POSTED], "one rail entry per save"
    by_name, in_detail = [
        step
        for step in streamed[-1][1]["trace"]
        if step["summary"].startswith(f"{TOOL_NAME}(")
    ]
    assert by_name["detail"] == BY_NAME
    assert in_detail["detail"] == IN_DETAIL
