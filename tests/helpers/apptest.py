"""Reading a rendered page. Cora draws an answer with a custom component so a citation
in it can be clicked, and AppTest's element proxies cannot see inside one: the payload
the component was mounted with is what a test reads instead."""

import json
import re
from html import unescape

from streamlit.testing.v1 import AppTest

ANSWER_COMPONENT = "cora_cited_answer"
PANE_COMPONENT = "cora_document_pane"
_TAG = re.compile(r"<[^>]+>")
_CLICKABLE = re.compile(r'data-cite="(\d+)"')


def mounted_html(at: AppTest, name: str) -> list[str]:
    """The HTML each mounted instance of one component was given."""
    return [
        json.loads(element.proto.json).get("html", "")
        for element in at.main
        if element.type == "bidi_component" and element.proto.component_name == name
    ]


def answers(at: AppTest) -> list[str]:
    return [_as_text(html) for html in mounted_html(at, ANSWER_COMPONENT)]


def newest_answer(at: AppTest) -> str:
    """The last thing the assistant said, whether it answered or failed. A failed turn
    draws an error instead of an answer component, so reaching for the newest answer
    finds nothing — and raising there would cost a failing assertion the message that
    was to explain it."""
    drawn = answers(at)
    if drawn:
        return drawn[-1]
    reported = [error.value for error in at.error]
    if reported:
        return reported[-1]
    return ""


def clickable_citations(at: AppTest) -> list[int]:
    """The numbers the newest answer offers as buttons. A model writes `[n]` whether or
    not a passage was registered under it, and a number the domain does not read as a
    citation — glued to a word, or inside a fence — never becomes one, so the text of an
    answer says nothing about what the reader can open. The button does.

    Newest, because a thread redraws every turn on every rerun: asked of the whole page,
    "this turn cited nothing" is answered by some earlier turn that did."""
    drawn = mounted_html(at, ANSWER_COMPONENT)
    if not drawn:
        return []
    found = (int(number) for number in _CLICKABLE.findall(drawn[-1]))
    return sorted(dict.fromkeys(found))


def page_text(at: AppTest) -> str:
    """Everything the page says, whichever element says it."""
    return "\n".join([*(md.value for md in at.markdown), *answers(at)])


def _as_text(html: str) -> str:
    return unescape(_TAG.sub("", html)).strip()
