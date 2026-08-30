"""What a plugin is: it is handed cora, and it registers what it has."""

import pytest

from app_builder import assembled
from cora.domain.errors import InputRejectedError
from cora.engine.plugin_registry import load_plugins
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

REGISTERING = "fixture_plugins.registering"
INSTRUCTIONS = "You are the registering test plugin. Echo what the user asks you to."
REFUSAL = "The registering plugin will not answer shouting."
ANSWER = "You said hello."
THREAD = "t1"


def _calling_echo() -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name="echo", arguments={"word": "hello"}, call_id="c1"),)
    )


@pytest.mark.integration
def test_a_plugin_registers_a_tool_an_instruction_and_a_rule() -> None:
    """All three contributions of one plugin, in one turn: the tool the model called,
    the instructions it was briefed with, and the rule that refused what came next."""
    model = ScriptedChatModel([_calling_echo(), ModelReply(text=ANSWER)])
    app = assembled(chat_model=model, plugins=load_plugins([REGISTERING]))

    answered = app.agent.answer("Say hello.", THREAD)

    assert answered.answer == ANSWER
    assert 'echo(word="hello")' in " ".join(step.summary for step in answered.trace)
    briefed = model.last_messages
    assert briefed is not None
    assert INSTRUCTIONS in briefed[0].content, (
        "the plugin's instructions head the brief"
    )

    with pytest.raises(InputRejectedError) as shouted:
        app.agent.answer("SAY HELLO", THREAD)

    assert shouted.value.user_message == REFUSAL
