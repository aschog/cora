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
SNATCH_WORKOUT = "Рывок гири"
ONE_ARM_SWING = "Мах одной рукой"  # noqa: RUF001
POSTED = [
    ("2026-09-18-12-27-51.md", "# Deadlift, conventional 14 kg\n3 sets of 10\n"),
    (
        "2026-09-18-16-20-05.md",
        f"{SNATCH_WORKOUT}\n\n# {ONE_ARM_SWING} 14 kg\n2 sets of 10\n",
    ),
]
BY_NAME = (
    f"2026-09-18: {SNATCH_WORKOUT} · untitled save: Deadlift, conventional\n"
    "1 day, 2 saves. The sets, reps and weights are in the details."
)


def test_the_summary_says_what_it_is_and_what_else_is_on_file() -> None:
    app = assembled(
        plugins=(load_plugin("cora.plugins.fitness"),),
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    text="",
                    tool_calls=(ToolCall(name=TOOL_NAME, arguments={}, call_id="c1"),),
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
                    "question": "Show all workouts",
                    "thread_id": "t1",
                    "pin": FITNESS,
                },
            ).text
        )

    [by_name] = [
        step
        for step in streamed[-1][1]["trace"]
        if step["summary"].startswith(f"{TOOL_NAME}(")
    ]
    assert by_name["detail"] == BY_NAME
