"""The screen `docs/cora_mockup.html` describes: documents down the left, the
conversation in the middle, and a rail on the right carrying what the answer rests on —
over conversations that are still there the next time the app starts."""

import pytest
from streamlit.testing.v1 import AppTest

from app_builder import assembled, indexed
from apptest import clickable_citations, open_document
from cora.app.assembly import App
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

DOCUMENT = "protein.md"
PASSAGE = "aim for 1.6 g of protein per kg of bodyweight"
SEED_DOC = (DOCUMENT, f"# Protein\n\nFor strength training, {PASSAGE}.\n".encode())
QUESTION = "How much protein should I eat?"
ANSWER = "Your notes say 1.6 g per kg [1]."
PANELS = ["Plan", "Source", "Sessions", "Memory"]


def _app(conversations_path) -> App:
    # The store is being built; the marker goes when the adapter lands.
    from cora.adapters.sqlite_conversations import (  # ty: ignore[unresolved-import]
        SqliteConversations,
    )

    return indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [
                    ModelReply(
                        tool_calls=(
                            ToolCall(
                                name=SEARCH_TOOL_NAME,
                                arguments={"query": "protein"},
                                call_id="call-1",
                            ),
                        )
                    ),
                    ModelReply(text=ANSWER),
                ]
            ),
            conversations=SqliteConversations(str(conversations_path)),
        ),
        SEED_DOC,
    )


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.frontends.streamlit.chat import render

    render(app)


def _said_in(container) -> str:
    """Everything one panel of the page says, whichever element says it."""
    return "\n".join(
        [
            *(element.value for element in container.markdown),
            *(element.value for element in container.code),
            *(element.value for element in container.text),
        ]
    )


@pytest.mark.integration
@pytest.mark.xfail(
    strict=True, reason="the rail and the stored conversation are in progress"
)
def test_the_page_is_three_rails_over_a_conversation_that_persists(tmp_path) -> None:
    """One criterion, read left to right: the documents rail, the conversation and its
    rail of four panels, the plan of the turn just taken, the passage it cites — and
    then the same store opened afresh, still listing the conversation to go back to."""
    store = tmp_path / "conversations.sqlite"
    at = AppTest.from_function(_page, args=(_app(store),)).run()

    assert at.sidebar.file_uploader, "documents are the left rail"
    conversation, rail = at.columns[:2]
    assert conversation.proto.weight > rail.proto.weight, (
        "the conversation is the wider"
    )
    assert [tab.label for tab in at.tabs] == PANELS
    assert conversation.chat_input, "the question is asked in the conversation's column"

    at.chat_input[0].set_value(QUESTION).run()

    assert not at.exception
    assert clickable_citations(at) == [1], "the answer cites the passage it rests on"
    plan, _source, _sessions, _memory = at.tabs
    assert SEARCH_TOOL_NAME in _said_in(plan), (
        "how the answer was reached is in the rail"
    )
    assert not conversation.expander, "and nowhere else"

    at.session_state["open_citation"] = 1
    at.run()

    assert open_document(at) == [DOCUMENT], "the citation still pops up over the chat"

    returning = AppTest.from_function(_page, args=(_app(store),)).run()

    assert not returning.exception
    _plan, _src, sessions, _mem = returning.tabs
    assert QUESTION in _said_in(sessions), "the conversation outlived the process"
