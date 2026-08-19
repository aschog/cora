import pytest
from streamlit.proto.Block_pb2 import Block
from streamlit.testing.v1 import AppTest

from app_builder import assembled, indexed
from apptest import (
    clickable_citations,
    mounted_html,
    mounted_html_in,
    newest_answer,
    open_dialogs,
    open_document,
)
from cora.app.assembly import App
from cora.domain.errors import LlmTimeoutError
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.streamlit.viewer import (
    _ANSWER_CSS,
    _PANE_CSS,
    ANSWER_COMPONENT,
    CITATION_COLOUR,
    LAST_CITATION,
    NO_DOCUMENT,
    NOT_KEPT,
    NOTHING_CITED,
    OPEN_CITATION,
    PANE_COMPONENT,
    UNKNOWN_CITATION,
)
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.documents import Documents
from cora.ports.plugin import ToolCall
from fakes import (
    FailingChatModel,
    FailingDocuments,
    KeepsNothingDocuments,
    ScriptedChatModel,
)

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


def _split(at: AppTest) -> list[float]:
    """How the page divides itself, the sidebar's own columns left out of it."""
    return [column.weight for column in at.main.columns]


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
    assert open_document(at) == []


def test_opening_a_citation_puts_its_document_over_the_chat() -> None:
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert open_document(at) == ["protein.md"]
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
    assert open_document(at) == ["creatine.md"]
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
    assert open_document(at) == ["protein.md"]


def test_the_popup_offers_no_second_way_out_of_its_own() -> None:
    """The title bar carries a cross already; a Close button under the title repeated it
    and cost the passage the rows it sat in."""
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    [popup] = open_dialogs(at)
    assert list(popup.button) == [], "the cross in the title bar is the only way out"


def _closing_page() -> None:  # AppTest re-executes this without the module's globals
    import streamlit as st

    from cora.frontends.streamlit.viewer import close_citation, open_citation

    close_citation()
    st.text(repr(open_citation()))


def test_closing_a_citation_clears_it() -> None:
    """What the Close button used to drive, pinned where it still can be. Dismissing a
    dialog runs off a widget delta the browser sends, so this is the last headless hold
    on the handler the popup is wired to."""
    at = AppTest.from_function(_closing_page)
    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert [line.value for line in at.text] == ["None"]


def test_a_citation_cleared_takes_the_document_with_it() -> None:
    at = _asked(_run(_one_citation()))
    at.session_state[OPEN_CITATION] = 1
    at.run()

    at.session_state[OPEN_CITATION] = None
    at.run()

    assert not at.exception
    assert _panes(at) == []
    assert open_document(at) == []


def test_a_number_from_no_answer_in_this_thread_opens_nothing() -> None:
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()
    at.session_state[OPEN_CITATION] = 9
    at.run()

    assert not at.exception
    assert _panes(at) == []
    assert UNKNOWN_CITATION in [warning.value for warning in at.warning]


def test_a_passage_whose_text_was_never_kept_says_so_under_its_title() -> None:
    """An index written before documents were kept still answers with citations, so the
    pane has to account for a passage it can name and cannot read. The title is what
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
    assert open_document(at) == ["protein.md"]
    assert _panes(at) == []
    assert NOT_KEPT in [warning.value for warning in at.warning]
    assert NOT_KEPT != UNKNOWN_CITATION, "a passage I cannot read is not a stray number"


def test_a_number_from_no_answer_is_titled_apart_from_a_passage_never_kept() -> None:
    """Two failures that look alike inside the popup and are not: one is a passage this
    conversation cites and cannot read, the other a number no answer ever wrote. The
    title is what separates them now the heading has gone — a document names the first,
    and nothing names the second."""
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 9
    at.run()

    assert not at.exception
    assert open_document(at) == [NO_DOCUMENT]
    assert UNKNOWN_CITATION in [warning.value for warning in at.warning]
    assert NO_DOCUMENT != "protein.md", "a stray number is not a document to open"


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


def test_the_popup_is_titled_with_the_document_and_names_it_only_once() -> None:
    """A filename set as a page heading broke over three lines and pushed the passage
    below the fold. The popup already carries a title bar, so the name belongs there —
    and stating it twice costs the passage the rows it was pushed down by."""
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    assert open_document(at) == ["protein.md"]
    assert "protein.md" not in _headings(at), (
        "the title names it, and nothing else does"
    )


def test_the_popup_is_no_wider_than_the_document_needs() -> None:
    """Large was most of the screen for a passage in a document, and it buried the chat
    it was opened from rather than sitting over it."""
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()

    [popup] = open_dialogs(at)
    assert popup.proto.dialog.width == Block.Dialog.DialogWidth.SMALL


def test_the_popup_can_be_dismissed_and_a_dismissal_is_handled() -> None:
    """Escape, the corner cross and a click outside all dismiss it, and a dismissal that
    left the citation open would redraw the popup on the very next rerun — the reader
    would have no way to be rid of it. Streamlit stamps a dialog with an id only once a
    dismiss handler is registered, so the id is what says one is there.

    AppTest cannot dismiss a dialog: the handler runs off a widget delta the browser
    sends. What the handler does is the Close button's test above, which drives the same
    `close_citation`."""
    at = _asked(_run(_one_citation()))

    at.session_state[OPEN_CITATION] = 1
    at.run()

    [popup] = open_dialogs(at)
    assert popup.proto.dialog.dismissible, "escaping it is how a reader gets back"
    assert popup.proto.dialog.id, "a dismissal nothing handles reopens for ever"


def test_the_passage_pops_up_over_a_chat_that_keeps_the_whole_page() -> None:
    """Splitting the page for the document was the wrong shape whichever way it ran: a
    third reads a document in fragments, two thirds costs the conversation its line. The
    passage is something to open, read and dismiss, so it arrives over the chat rather
    than beside it — and the conversation behind it gives up none of the width it had.

    Read as "unchanged" rather than "none", because the page carries a split of its own
    now: the conversation and the rail beside it. What this holds is that opening a
    passage is not what moves it."""
    at = _asked(_run(_one_citation()))
    unopened = _split(at)

    at.session_state[OPEN_CITATION] = 1
    at.run()

    assert not at.exception
    [pane] = _panes(at)
    assert "1.6 g of protein" in pane
    assert _split(at) == unopened, "the chat keeps the page the dialog is drawn over"


def test_an_answer_with_citations_offers_no_sources_panel() -> None:
    """The numbers in the answer are the way into a document, and the panel listed the
    same passages a click away under every answer that had any."""
    at = _asked(_run(_one_citation()))

    assert not at.exception
    assert [panel.label for panel in at.expander] == []


def test_the_citation_colour_dresses_both_the_button_and_the_passage_it_opens() -> None:
    """One colour for the click and for what the click reveals: on the theme's primary
    the passage wore whatever the buttons wore by coincidence, and a filled mark took
    the theme's *background* for its text — white on amber, once the fill stopped being
    the dark red the default ships."""
    assert f"color: {CITATION_COLOUR}" in _ANSWER_CSS
    assert f"color: {CITATION_COLOUR}" in _PANE_CSS
    assert "var(--st-primary-color)" not in _PANE_CSS
    assert "background: var(--st-background-color)" not in _PANE_CSS


def test_a_number_glued_to_a_word_is_not_a_citation_the_reader_can_click() -> None:
    """What the live tier's positive checks rest on. Both numbers were registered by
    the same search, so what tells them apart is the domain's rule alone: `[1]` after a
    space is a citation, `bodyweight[2]` is a bracket the model wrote into a word. The
    answer carries both, and only one of them opens anything."""
    at = _asked(
        _run(
            _app(
                ScriptedChatModel(
                    [
                        _searching("c1", "protein"),
                        ModelReply(
                            text="Your notes say 1.6 g [1], per kg bodyweight[2]."
                        ),
                    ]
                )
            )
        )
    )

    assert not at.exception
    [answer] = _mounted(at, ANSWER_COMPONENT)
    assert "bodyweight[2]" in answer, "the number the model glued on reaches the page"
    assert clickable_citations(at) == [1], "only the one the domain read as a citation"


def test_the_citations_reported_are_the_newest_answers_not_the_whole_threads() -> None:
    """A thread redraws every answer on every rerun, so a page holds every turn's
    buttons at once. A check that a turn cited nothing has to be asked of that turn."""
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

    at.chat_input[0].set_value("hi").run()

    assert not at.exception
    assert len(_mounted(at, ANSWER_COMPONENT)) == 2, "both turns are on the page"
    assert clickable_citations(at) == [], "the newest turn cited nothing"


def test_the_very_first_turn_failing_is_reported_and_not_read_as_an_answer() -> None:
    """The same rule where there is no earlier turn to be confused with: the page holds
    an error and no answer, and asking for the answer says so rather than handing back
    the error to be searched for words it was never going to contain."""
    at = _asked(_run(_app(FailingChatModel(LlmTimeoutError()))))

    assert not at.exception, "the failure is reported, not raised"
    assert _mounted(at, ANSWER_COMPONENT) == [], "no answer was drawn"
    with pytest.raises(AssertionError, match="took too long"):
        newest_answer(at)


def _answers_then_fails() -> ChatModel:
    class AnswersThenFails:
        calls = 0

        def complete(
            self, messages: object, tools: object, on_text: object = None
        ) -> ModelReply:
            AnswersThenFails.calls += 1
            if AnswersThenFails.calls == 1:
                return _searching("c1", "protein")
            if AnswersThenFails.calls == 2:
                return ModelReply(text=CITED)
            raise LlmTimeoutError()

    AnswersThenFails.calls = 0
    return AnswersThenFails()


def test_a_turn_that_failed_reports_neither_the_last_answer_nor_its_citations() -> None:
    """The trap three rounds of patching walked into: a thread redraws every turn on
    every rerun, so the newest answer *on the page* belongs to the newest turn that
    answered — not to the newest turn. After one good turn, a failed one reported the
    good one's words and its citations as though it had said them."""
    at = _asked(_run(_app(_answers_then_fails())))

    at.chat_input[0].set_value("Hi there!").run()

    assert not at.exception
    assert [error.value for error in at.error], "the turn failed and says so"
    assert clickable_citations(at) == [], (
        "the earlier turn's citations are not this one's"
    )


def test_reading_the_answer_of_a_turn_that_gave_none_fails_and_says_what_happened() -> (
    None
):
    """Loud, not empty: a helper that hands back the error text lets `assert X not in
    answer` pass while the model never answered, which is worse than the raise it
    replaced. The message carries what the chat said, so the failure explains itself."""
    at = _asked(_run(_app(_answers_then_fails())))
    at.chat_input[0].set_value("Hi there!").run()

    with pytest.raises(AssertionError, match="took too long"):
        newest_answer(at)


def _source_panel(at: AppTest):
    _plan, source, _sessions, _memory = at.tabs
    return source


def test_the_source_panel_says_what_it_is_for_before_anything_is_cited() -> None:
    at = _asked(_run(_one_citation()))

    assert not at.exception
    assert NOTHING_CITED in [line.value for line in _source_panel(at).caption]


def test_the_source_panel_shows_the_passage_last_read() -> None:
    """The same passage the popup marks, in the rail beside the conversation."""
    at = _asked(_run(_one_citation()))

    at.session_state[LAST_CITATION] = 1
    at.run()

    assert not at.exception
    [passage] = mounted_html_in(_source_panel(at), PANE_COMPONENT)
    assert "1.6 g of protein" in passage
    assert "<mark" in passage, (
        "the cited span is marked in the rail as it is in the popup"
    )


def test_the_source_panel_keeps_the_passage_after_the_popup_is_dismissed() -> None:
    """Dismissing clears the citation that is *open*; what was last read stays, or the
    panel is empty except while the popup covers it."""
    at = _asked(_run(_one_citation()))
    at.session_state[LAST_CITATION] = 1
    at.session_state[OPEN_CITATION] = 1
    at.run()

    at.session_state[OPEN_CITATION] = None
    at.run()

    assert not at.exception
    assert open_document(at) == [], "the popup is gone"
    assert mounted_html_in(_source_panel(at), PANE_COMPONENT), "the passage is not"


def _dismissing_page() -> None:  # AppTest re-executes this without the module's globals
    import streamlit as st

    from cora.frontends.streamlit.viewer import (
        close_citation,
        last_citation,
        open_citation,
    )

    close_citation()
    st.text(repr((open_citation(), last_citation())))


def test_dismissing_a_citation_keeps_the_passage_it_showed() -> None:
    """Dismissal clears what is *open*, not what was last read. Driven through the
    handler because the cross that runs it is out of AppTest's reach — and asserted on
    the handler because a page-level test can set the state it claims to be testing."""
    at = AppTest.from_function(_dismissing_page)
    at.session_state[OPEN_CITATION] = 1
    at.session_state[LAST_CITATION] = 1
    at.run()

    assert not at.exception
    assert [line.value for line in at.text] == ["(None, 1)"]
