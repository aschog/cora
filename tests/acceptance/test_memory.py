"""The outer test for story 3."""

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

from apptest import page_text
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

FACT = "The user is vegetarian."
SHARED = "I'm vegetarian — keep that in mind."
ACKNOWLEDGED = "Noted, I'll remember that."
LATER = "What should I eat after training?"
ADVICE = "Lentils and tofu rebuild protein after a session."


def _remembering() -> ModelReply:
    from cora.engine.memory_tool import REMEMBER_TOOL_NAME

    return ModelReply(
        tool_calls=(
            ToolCall(name=REMEMBER_TOOL_NAME, arguments={"fact": FACT}, call_id="m1"),
        )
    )


def _memory_at(path: pathlib.Path):
    from cora.adapters.sqlite_store_memory import SqliteStoreMemory

    return SqliteStoreMemory.at(str(path))


def _app(memory, chat_model: ChatModel):
    from app_builder import assembled

    return assembled(chat_model=chat_model, memory=memory)


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.frontends.streamlit.chat import render

    render(app)


def _session(app, question: str) -> AppTest:
    at = AppTest.from_function(_page, args=(app,)).run()
    at.chat_input[0].set_value(question).run()
    return at


def _visible(at: AppTest) -> str:
    return page_text(at)


def _memory_panel(at: AppTest):
    """The rail's memory panel. What cora remembers moved out of the sidebar when the
    page took the mockup's shape; the sidebar is documents now."""
    _plan, _source, _sessions, panel = at.tabs
    return panel


def _remembered(at: AppTest) -> str:
    return "\n".join(md.value for md in _memory_panel(at).markdown)


@pytest.mark.integration
def test_a_fact_shared_last_session_briefs_the_model_the_next(
    tmp_path: pathlib.Path,
) -> None:
    """The criterion end to end: one session tells it something, a fresh session over
    the same memory file answers with it in hand and shows what it is holding."""
    path = tmp_path / "memory.sqlite"
    told = ScriptedChatModel([_remembering(), ModelReply(text=ACKNOWLEDGED)])
    first = _session(_app(_memory_at(path), told), SHARED)
    assert not first.exception

    asked = ScriptedChatModel([ModelReply(text=ADVICE)])
    at = _session(_app(_memory_at(path), asked), LATER)

    assert not at.exception
    assert ADVICE in _visible(at)
    assert asked.last_messages is not None
    assert FACT in asked.last_messages[0].content
    assert FACT in _remembered(at)


@pytest.mark.integration
def test_clearing_the_panel_empties_the_store_and_the_next_brief(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "memory.sqlite"
    told = ScriptedChatModel([_remembering(), ModelReply(text=ACKNOWLEDGED)])
    _session(_app(_memory_at(path), told), SHARED)

    asked = ScriptedChatModel([ModelReply(text=ADVICE), ModelReply(text=ADVICE)])
    at = _session(_app(_memory_at(path), asked), LATER)
    assert asked.last_messages is not None
    assert FACT in asked.last_messages[0].content

    _memory_panel(at).button(key="clear_memory").click().run()
    at.chat_input[0].set_value(LATER).run()

    assert not at.exception
    assert FACT not in _remembered(at)
    assert FACT not in asked.last_messages[0].content
