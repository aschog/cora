import re

import pytest
from streamlit.testing.v1 import AppTest

from app_builder import assembled, indexed
from apptest import PANE_COMPONENT, mounted_html, open_document, page_text
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


def _app() -> App:
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
            )
        ),
        SEED_DOC,
    )


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.frontends.streamlit.chat import render

    render(app)


def _panes(at: AppTest) -> list[str]:
    return mounted_html(at, PANE_COMPONENT)


@pytest.mark.integration
def test_a_cited_passage_opens_over_the_chat_and_closes_again() -> None:
    """The click that opens it is a component's, out of AppTest's reach, so the state
    the click writes is what this drives. What the popup does with it is the criterion:
    the cited document, that passage marked, and the chat back after closing."""
    at = AppTest.from_function(_page, args=(_app(),)).run()

    at.chat_input[0].set_value(QUESTION).run()

    assert not at.exception
    assert ANSWER in page_text(at)
    assert _panes(at) == [], "nothing is open until a citation is clicked"

    at.session_state["open_citation"] = 1
    at.run()

    assert not at.exception
    assert open_document(at) == [DOCUMENT]
    [pane] = _panes(at)
    [marked] = re.findall(r"<mark[^>]*>(.*?)</mark>", pane, re.DOTALL)
    assert PASSAGE in marked, f"the cited passage is not marked in the pane: {pane!r}"

    at.button(key="close_citation").click().run()

    assert not at.exception
    assert _panes(at) == []
    assert open_document(at) == []
    assert at.chat_input
