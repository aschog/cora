"""A plugin keeps what it worked out, and a later turn of the conversation reads it.

The plugin, its registration and both whole turns are the real ones; the model is
scripted, which is the boundary a stub is for.
"""

from app_builder import assembled
from cora.domain.chat_result import ChatResult
from cora.domain.trace import ToolUse
from cora.engine.plugin_registry import load_plugins
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from fixture_plugins.keeping import KEEP_TOOL, NOTHING, READ_TOOL

KEEPER = "fixture_plugins.keeping"
THREAD = "kept"
SETTLED = "Kyoto in the second week of May"
FIRST = "Let us say Kyoto, second week of May."
SECOND = "What did we settle on?"
NOTED = "Noted."
RECALLED = "You settled on Kyoto in the second week of May."


def _calling(name: str, **arguments: str) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=name, arguments=dict(arguments), call_id=name),)
    )


def _read(answered: ChatResult) -> list[str]:
    return [
        step.detail
        for step in answered.trace
        if isinstance(step, ToolUse) and step.name == READ_TOOL
    ]


def test_what_one_turn_kept_the_next_turn_reads_back() -> None:
    app = assembled(
        chat_model=ScriptedChatModel(
            [
                _calling(KEEP_TOOL, text=SETTLED),
                ModelReply(text=NOTED),
                _calling(READ_TOOL),
                ModelReply(text=RECALLED),
            ]
        ),
        plugins=load_plugins([KEEPER]),
    )

    app.agent.answer(FIRST, THREAD)
    answered = app.agent.answer(SECOND, THREAD)

    assert _read(answered) == [SETTLED]
    assert answered.answer == RECALLED


def test_a_plugin_that_wrote_while_loading_kept_nothing() -> None:
    app = assembled(
        chat_model=ScriptedChatModel([_calling(READ_TOOL), ModelReply(text=NOTED)]),
        plugins=load_plugins([KEEPER]),
    )

    answered = app.agent.answer(SECOND, THREAD)

    assert _read(answered) == [NOTHING]


def test_a_second_conversation_reads_nothing_of_the_first_ones_values() -> None:
    app = assembled(
        chat_model=ScriptedChatModel(
            [
                _calling(KEEP_TOOL, text=SETTLED),
                ModelReply(text=NOTED),
                _calling(READ_TOOL),
                ModelReply(text=NOTED),
            ]
        ),
        plugins=load_plugins([KEEPER]),
    )

    app.agent.answer(FIRST, THREAD)
    answered = app.agent.answer(SECOND, "elsewhere")

    assert _read(answered) == [NOTHING]


def test_a_deleted_conversation_keeps_nothing_behind() -> None:
    app = assembled(
        chat_model=ScriptedChatModel(
            [
                _calling(KEEP_TOOL, text=SETTLED),
                ModelReply(text=NOTED),
                _calling(READ_TOOL),
                ModelReply(text=NOTED),
            ]
        ),
        plugins=load_plugins([KEEPER]),
    )
    app.agent.answer(FIRST, THREAD)

    app.agent.forget(THREAD)
    answered = app.agent.answer(SECOND, THREAD)

    assert _read(answered) == [NOTHING]


def test_deleting_one_conversation_leaves_anothers_values_alone() -> None:
    app = assembled(
        chat_model=ScriptedChatModel(
            [
                _calling(KEEP_TOOL, text=SETTLED),
                ModelReply(text=NOTED),
                _calling(KEEP_TOOL, text=SETTLED),
                ModelReply(text=NOTED),
                _calling(READ_TOOL),
                ModelReply(text=RECALLED),
            ]
        ),
        plugins=load_plugins([KEEPER]),
    )
    app.agent.answer(FIRST, THREAD)
    app.agent.answer(FIRST, "kept-too")

    app.agent.forget(THREAD)
    answered = app.agent.answer(SECOND, "kept-too")

    assert _read(answered) == [SETTLED]
