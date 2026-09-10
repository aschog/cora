"""The outer test for the shape a plugin may ask a delegated loop for."""

import json
from typing import Any

from app_builder import assembled
from cora.engine.host import ANSWER_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension, Host
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

THREAD = "the-shape-i-asked-for"
QUESTION = "What did the sub-agent find?"
ANSWER = "It found two things, and I read them off the shape."
SCOPE = "shaped"
TOOL_NAME = "gather"
SHAPE: dict[str, Any] = {
    "type": "object",
    "properties": {
        "found": {"type": "array", "items": {"type": "string"}},
        "note": {"type": "string"},
    },
    "required": ["found"],
    "additionalProperties": False,
}
VALUE: dict[str, Any] = {"found": ["one", "two"], "note": "both from the documents"}


def test_a_plugin_asks_a_delegated_loop_for_a_shape_and_is_handed_the_value() -> None:
    """The story: a tool that needs a value declares its shape, and what comes back is
    that value — no string to find JSON in, and nothing to fall back to."""
    handed: list[Any] = []
    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(ToolCall(name=TOOL_NAME, arguments={}, call_id="t1"),)
            ),
            # The loop's own round: it answers by calling what the shape named.
            ModelReply(
                tool_calls=(
                    ToolCall(name=ANSWER_TOOL_NAME, arguments=VALUE, call_id="a1"),
                )
            ),
            ModelReply(text=ANSWER),
        ]
    )
    app = assembled(
        chat_model=model,
        plugins=(
            Extension(module="fixture_plugins.shaped", extend=_gathering(handed)),
        ),
        scopes=(SCOPE,),
    )

    answered = app.agent.answer(QUESTION, THREAD)

    assert handed == [VALUE], "the tool was handed the value, parsed by nobody"
    assert answered.answer == ANSWER
    assert json.dumps(VALUE) in _asked_of(model), "the value reached the model as JSON"


def _gathering(handed: list[Any]) -> Any:
    """A plugin whose one tool delegates a loop and needs its answer shaped."""

    def extend(cora: Host) -> None:
        def gather() -> Any:
            found = cora.delegate("Find two things.", shape=SHAPE)
            handed.append(found)
            return found

        cora.register_tool(
            name=TOOL_NAME,
            description="Gather two things.",
            parameter_schema={"type": "object", "properties": {}},
            run=gather,
            scope=SCOPE,
        )

    return extend


def _asked_of(model: ScriptedChatModel) -> str:
    return "\n".join(message.content for message in model.last_messages or ())
