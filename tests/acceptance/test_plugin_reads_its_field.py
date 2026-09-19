"""The outer test for the story: a plugin's tool is handed every document its field
holds, by name and by text, and nothing of another field's."""

from typing import Any

import pytest

from app_builder import assembled, indexed
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension, Host
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

THREAD = "what-the-field-holds"
FIELD = "logs"
OTHER = "elsewhere"
TOOL_NAME = "list_logs"
# One name saved twice, as a trainer saving twice on one day does.
NAME = "2026-09-18.md"
FIRST = "# Deadlift 14 kg\n3 sets of 10\n"
SECOND = "# Swing 14 kg\n2 sets of 10\n"
ELSEWHERE = "# Not this field's\n"


@pytest.mark.xfail(
    strict=True, reason="the host hands a plugin search and nothing else"
)
def test_a_plugins_tool_is_handed_what_its_field_holds() -> None:
    handed: list[Any] = []
    app = assembled(
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    tool_calls=(ToolCall(name=TOOL_NAME, arguments={}, call_id="t1"),)
                ),
                ModelReply(text="Listed."),
            ]
        ),
        plugins=(Extension(module="fixture_plugins.logs", extend=_listing(handed)),),
        scopes=(FIELD, OTHER),
    )
    indexed(app, (NAME, FIRST.encode()), (NAME, SECOND.encode()), scope=FIELD)
    indexed(app, (NAME, ELSEWHERE.encode()), scope=OTHER)

    app.agent.answer("What is in the log?", THREAD, pin=FIELD)

    assert [(each.name, each.text) for each in handed] == [
        (NAME, FIRST),
        (NAME, SECOND),
    ]


def _listing(handed: list[Any]) -> Any:
    def extend(cora: Host) -> None:
        def list_logs() -> str:
            # The port has no such question yet: the ignore leaves with the marker.
            handed.extend(cora.documents.all())  # ty: ignore[unresolved-attribute]
            return "\n".join(each.text for each in handed)

        cora.register_tool(
            name=TOOL_NAME,
            description="Every log the field holds.",
            parameter_schema={"type": "object", "properties": {}},
            run=list_logs,
            scope=FIELD,
        )

    return extend
