"""Reading a rendered page. Cora draws an answer with a custom component so a citation
in it can be clicked, and AppTest's element proxies cannot see inside one: the payload
the component was mounted with is what a test reads instead."""

import json
import re
from collections.abc import Iterator
from html import unescape
from typing import Any

from streamlit.testing.v1 import AppTest

ANSWER_COMPONENT = "cora_cited_answer"
PANE_COMPONENT = "cora_document_pane"
THREAD = "messages"
_TAG = re.compile(r"<[^>]+>")
_CLICKABLE = re.compile(r'data-cite="(\d+)"')


def mounted_html(at: AppTest, name: str) -> list[str]:
    """The HTML each mounted instance of one component was given.

    Read off the whole tree rather than `at.main`, because a dialog's contents are not
    in the main container: the cited passage is drawn inside one, and a reader looking
    only at `at.main` finds an empty page and calls it "no passage opened"."""
    return [
        json.loads(node.proto.json).get("html", "")
        for node in _nodes(at)
        if getattr(node, "type", None) == "bidi_component"
        and node.proto.component_name == name
    ]


def open_dialogs(at: AppTest) -> list[Any]:
    """The popups on the page, as the blocks that describe them."""
    return [
        node.proto.dialog
        for node in _nodes(at)
        if getattr(node, "type", None) == "dialog"
    ]


def open_document(at: AppTest) -> list[str]:
    """The document each open popup is named after. A cited passage arrives in one over
    the chat, so what names it is the popup's title, not a heading on the page."""
    return [dialog.title for dialog in open_dialogs(at)]


def _nodes(at: AppTest) -> Iterator[Any]:
    """Every node of the page. AppTest offers no public walk of the whole tree, and its
    containers stop short of the one a dialog is drawn in."""
    return iter(at._tree)


def answers(at: AppTest) -> list[str]:
    return [_as_text(html) for html in mounted_html(at, ANSWER_COMPONENT)]


def newest_turn_failed(at: AppTest) -> bool:
    """Whether the newest thing the assistant said was a failure rather than an answer.

    Read off the thread, not off the page: every turn is redrawn on every rerun, so the
    newest answer *on the page* belongs to the newest turn that answered, which after a
    failure is not the newest turn."""
    # SIM401's `.get(...)` is not available here: AppTest's session state is a proxy
    # that raises `KeyError` from `get` rather than returning the default.
    thread = at.session_state[THREAD] if THREAD in at.session_state else []  # noqa: SIM401
    spoken = [entry for entry in thread if entry.get("role") == "assistant"]
    return bool(spoken) and "error" in spoken[-1]


def newest_answer(at: AppTest) -> str:
    """The answer the newest turn gave, or a failure saying why there is none.

    It raises rather than substituting the error text, because most of what reads an
    answer asks whether something is *absent* from it — and an error standing in for an
    answer satisfies that quietly, leaving a check green over a turn the model never
    answered. The message carries what the chat reported, so a run this happens in still
    explains itself."""
    drawn = answers(at)
    if newest_turn_failed(at) or not drawn:
        raise AssertionError(f"the newest turn gave no answer: {_reported(at)}")
    return drawn[-1]


def _reported(at: AppTest) -> list[str]:
    """The chat's errors, not the page's: a sidebar that cannot reach the memory store
    is reporting its own trouble, not this turn's."""
    return [error.value for error in at.main.error]


def clickable_citations(at: AppTest) -> list[int]:
    """The numbers the newest answer offers as buttons. A model writes `[n]` whether or
    not a passage was registered under it, and a number the domain does not read as a
    citation — glued to a word, or inside a fence — never becomes one, so the text of an
    answer says nothing about what the reader can open. The button does.

    Newest, because a thread redraws every turn on every rerun: asked of the whole page,
    "this turn cited nothing" is answered by some earlier turn that did."""
    drawn = mounted_html(at, ANSWER_COMPONENT)
    if newest_turn_failed(at) or not drawn:
        return []
    found = (int(number) for number in _CLICKABLE.findall(drawn[-1]))
    return sorted(dict.fromkeys(found))


def page_text(at: AppTest) -> str:
    """Everything the page says, whichever element says it."""
    return "\n".join([*(md.value for md in at.markdown), *answers(at)])


def _as_text(html: str) -> str:
    return unescape(_TAG.sub("", html)).strip()
