import pytest
from streamlit.testing.v1 import AppTest

from app_builder import assembled, indexed
from apptest import mounted_html
from cora.app.assembly import App
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.streamlit.viewer import (
    ANSWER_COMPONENT,
    CLOSE_KEY,
    NOT_KEPT,
    OPEN_CITATION,
    PANE_COMPONENT,
    UNKNOWN_CITATION,
)
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.documents import Documents
from cora.ports.plugin import ToolCall
from fakes import FailingDocuments, KeepsNothingDocuments, ScriptedChatModel

pytestmark = pytest.mark.integration
"""Every test here drives a Streamlit page, which is what the marker is for: the unit
tier is the watch layer, and `test_formatting.py` is where this feature's pure half is
covered."""

PROTEIN = ("protein.md", b"Aim for 1.6 g of protein per kg of bodyweight.")
CREATINE = ("creatine.md", b"Five grams of creatine a day is plenty.")
CITED = "Your notes say 1.6 g per kg [1]."
CITED_AGAIN = "And creatine is 5 g a day [2]."
THREAD_KEY = "messages"


def _searching(call_id: str, query: str) -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=SEARCH_TOOL_NAME, arguments={"query": query}, call_id=call_id
            ),
        )
    )


def _app(model: ChatModel, documents: Documents | None = None) -> App:
    return indexed(assembled(chat_model=model, documents=documents), PROTEIN, CREATINE)


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.frontends.streamlit.chat import render

    render(app)


def _run(app: App) -> AppTest:
    return AppTest.from_function(_page, args=(app,)).run()


def _mounted(at: AppTest, name: str) -> list[str]:
    return mounted_html(at, name)


def _panes(at: AppTest) -> list[str]:
    return _mounted(at, PANE_COMPONENT)


def _headings(at: AppTest) -> list[str]:
    return [heading.value for heading in at.header]


def _asked(at: AppTest, question: str = "How much protein?") -> AppTest:
    at.chat_input[0].set_value(question).run()
    return at


def _one_citation() -> App:
    return _app(
        ScriptedChatModel([_searching("c1", "protein"), ModelReply(text=CITED)])
    )


def test_a_thread_with_nothing_open_shows_no_document() -> None:
    at = _asked(_run(_one_citation()))

    assert not at.exception
    assert _panes(at) == []
    assert "protein.md" not in _headings(at)


def test_opening_a_citation_puts_its_document_beside_the_chat() -> None:
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert "protein.md" in _headings(at)
    [pane] = _panes(at)
    assert "1.6 g of protein" in pane
    assert at.chat_input, "the chat stays usable with a document open"


def test_the_pane_shows_the_document_the_citation_names() -> None:
    """Two documents are cited in one thread, so opening `[2]` may not show `[1]`."""
    at = _asked(
        _run(
            _app(
                ScriptedChatModel(
                    [
                        _searching("c1", "protein"),
                        ModelReply(text=CITED),
                        _searching("c2", "creatine"),
                        ModelReply(text=CITED_AGAIN),
                    ]
                )
            )
        )
    )
    at.chat_input[0].set_value("And creatine?").run()

    at.session_state[OPEN_CITATION] = 2
    at.run()

    assert not at.exception
    assert "creatine.md" in _headings(at)
    [pane] = _panes(at)
    assert "creatine" in pane
    assert "protein" not in pane


def test_a_citation_from_an_earlier_answer_still_opens() -> None:
    """The registry spans the thread: `[1]` found two turns ago is still `[1]`."""
    at = _asked(
        _run(
            _app(
                ScriptedChatModel(
                    [
                        _searching("c1", "protein"),
                        ModelReply(text=CITED),
                        ModelReply(text="Hello!"),
                    ]
                )
            )
        )
    )
    at.chat_input[0].set_value("Hi there!").run()

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert "protein.md" in _headings(at)


def test_closing_the_pane_takes_the_document_with_it() -> None:
    at = _asked(_run(_one_citation()))
    at.session_state[OPEN_CITATION] = 1
    at.run()

    at.button(key=CLOSE_KEY).click().run()

    assert not at.exception
    assert _panes(at) == []
    assert "protein.md" not in _headings(at)
    assert at.session_state[OPEN_CITATION] is None


def test_a_number_from_no_answer_in_this_thread_opens_nothing() -> None:
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()
    at.session_state[OPEN_CITATION] = 9
    at.run()

    assert not at.exception
    assert _panes(at) == []
    assert UNKNOWN_CITATION in [warning.value for warning in at.warning]


def test_a_passage_whose_text_was_never_kept_says_so_under_its_heading() -> None:
    """An index written before documents were kept still answers with citations, so the
    pane has to account for a passage it can name and cannot read. The heading is what
    tells this apart from a number belonging to no answer at all."""
    at = _asked(
        _run(
            _app(
                ScriptedChatModel(
                    [_searching("c1", "protein"), ModelReply(text=CITED)]
                ),
                documents=KeepsNothingDocuments(),
            )
        )
    )

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert "protein.md" in _headings(at)
    assert _panes(at) == []
    assert NOT_KEPT in [warning.value for warning in at.warning]
    assert NOT_KEPT != UNKNOWN_CITATION, "a passage I cannot read is not a stray number"


def test_a_store_that_cannot_be_read_is_reported_and_costs_the_chat_nothing() -> None:
    at = _asked(
        _run(
            _app(
                ScriptedChatModel(
                    [_searching("c1", "protein"), ModelReply(text=CITED)]
                ),
                documents=FailingDocuments(),
            )
        )
    )

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert at.error, "the pane says the document could not be read"
    assert at.chat_input
    assert at.session_state[THREAD_KEY], "the conversation is still on screen"


def test_the_answer_reaches_the_page_only_through_its_own_component() -> None:
    """Where an answer lives, pinned: it is drawn by the component that makes each `[n]`
    clickable, and nothing prints it as markdown. A test reading answers off
    `at.markdown` would pass on an empty page, which is how three live-tier assertions
    quietly stopped checking anything."""
    at = _asked(_run(_one_citation()))

    [answer] = _mounted(at, ANSWER_COMPONENT)
    assert 'data-cite="1"' in answer
    assert CITED not in "\n".join(md.value for md in at.markdown)


def test_the_chat_shares_the_page_only_while_a_document_is_open() -> None:
    """The criterion's other half: closing the pane gives the conversation its width
    back, which is the column split going away rather than a pane merely emptying."""
    at = _asked(_run(_one_citation()))

    assert at.columns == []

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert len(at.columns) == 2

    at.button(key=CLOSE_KEY).click().run()

    assert at.columns == []
