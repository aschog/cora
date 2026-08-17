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


def mounted_html(at: AppTest, name: str) -> list[str]:
    """The HTML each mounted instance of one component was given."""
    return [
        json.loads(element.proto.json).get("html", "")
        for element in at.main
        if element.type == "bidi_component" and element.proto.component_name == name
    ]


def answers(at: AppTest) -> list[str]:
    return [_as_text(html) for html in mounted_html(at, ANSWER_COMPONENT)]


def page_text(at: AppTest) -> str:
    """Everything the page says, whichever element says it."""
    return "\n".join([*(md.value for md in at.markdown), *answers(at)])


def _as_text(html: str) -> str:
    return unescape(_TAG.sub("", html)).strip()
