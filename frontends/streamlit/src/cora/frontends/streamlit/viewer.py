from collections.abc import Sequence
from typing import Any

import streamlit as st
import streamlit.components.v2
from cora.domain.citations import Citation
from cora.domain.errors import AdapterError
from cora.engine.knowledge_base import KnowledgeBase
from cora.frontends.streamlit.formatting import answer_html, document_html

OPEN_CITATION = "open_citation"
CLICKED = "clicked"
NOT_KEPT = "I no longer have the text of that document, so I cannot show the passage."
UNKNOWN_CITATION = "That citation does not belong to any answer in this conversation."
NO_DOCUMENT = "Citation"
PANE_WIDTH = "small"
ANSWER_COMPONENT = "cora_cited_answer"
PANE_COMPONENT = "cora_document_pane"
CITATION_COLOUR = "#f0c674"
"""One colour for a citation wherever it appears: the button that opens a passage and
the passage it opens. Named here rather than taken from the theme because the theme's
primary is the colour of everything else clickable, which left the passage looking like
an accident of the palette."""

_CITE_SLOT = "__CITE__"
"""Substituted into the stylesheets below rather than interpolated, so what is written
here stays CSS a browser would accept and a reader can scan."""

_ANSWER_HTML = "<div id='answer'></div>"
_ANSWER_CSS = """
#answer {
  color: var(--st-text-color);
  font-family: var(--st-font);
}
button.cite {
  background: none;
  border: none;
  padding: 0 0.1rem;
  color: __CITE__;
  cursor: pointer;
  font: inherit;
}
button.cite:hover {
  text-decoration: underline;
}
"""
_ANSWER_JS = """
export default function (component) {
  const { data, parentElement, setTriggerValue } = component
  const answer = parentElement.querySelector("#answer")
  if (!answer) return
  answer.innerHTML = data.html
  answer.querySelectorAll("button.cite").forEach((button) => {
    button.onclick = () => setTriggerValue("clicked", Number(button.dataset.cite))
  })
}
"""
_PANE_HTML = "<article id='document'></article>"
_PANE_CSS = """
#document {
  color: var(--st-text-color);
  font-family: var(--st-font);
  white-space: pre-wrap;
  max-height: 70vh;
  overflow-y: auto;
}
#document mark {
  background: none;
  color: __CITE__;
}
"""
_PANE_JS = """
export default function (component) {
  const { data, parentElement } = component
  const document_ = parentElement.querySelector("#document")
  if (!document_) return
  document_.innerHTML = data.html
  document_.querySelector("mark")?.scrollIntoView({block: "center"})
}
"""
_ANSWER_CSS = _ANSWER_CSS.replace(_CITE_SLOT, CITATION_COLOUR)
_PANE_CSS = _PANE_CSS.replace(_CITE_SLOT, CITATION_COLOUR)

_mounts: dict[str, Any] = {}


def declare_components() -> None:
    """Once per run, from the one place a run starts. The registry belongs to the
    running Streamlit runtime rather than to this module, so a component declared when
    the module was imported is not in the registry of the runtime that renders it."""
    _mounts[ANSWER_COMPONENT] = st.components.v2.component(
        ANSWER_COMPONENT, html=_ANSWER_HTML, css=_ANSWER_CSS, js=_ANSWER_JS
    )
    _mounts[PANE_COMPONENT] = st.components.v2.component(
        PANE_COMPONENT, html=_PANE_HTML, css=_PANE_CSS, js=_PANE_JS
    )


def cited_answer(answer: str, citations: Sequence[Citation], *, key: str) -> None:
    """The answer, with every citation in it a button. A click travels back as a
    trigger, and the callback is what opens the pane — by the time a result could be
    read, the script body has already drawn it."""
    _mount(ANSWER_COMPONENT)(
        key=key,
        data={"html": answer_html(answer, citations)},
        on_clicked_change=_opening(key),
    )


def open_citation() -> int | None:
    return st.session_state.get(OPEN_CITATION)


def close_citation() -> None:
    st.session_state[OPEN_CITATION] = None


def document_pane(knowledge_base: KnowledgeBase, citation: Citation | None) -> None:
    """The passage, over the chat rather than beside it. The dialog is decorated per run
    because its title is the document's name, which is only known once a citation has
    been clicked; dismissing it clears that citation, so the next rerun does not reopen
    what the reader just closed."""
    titled = citation.document if citation is not None else NO_DOCUMENT
    opening = st.dialog(titled, width=PANE_WIDTH, on_dismiss=close_citation)
    opening(_passage)(knowledge_base, citation)


def _passage(knowledge_base: KnowledgeBase, citation: Citation | None) -> None:
    """What the reader came for: the document, the cited passage marked and scrolled to,
    and a way out. A citation whose text was never kept says so rather than showing an
    empty page, and a store that cannot be read is reported here — the conversation
    behind it is unaffected either way. The document is named by the dialog's title and
    left by the cross beside it, so nothing here repeats either."""
    if citation is None:
        st.warning(UNKNOWN_CITATION)
        return
    try:
        text = knowledge_base.text(citation.upload)
    except AdapterError as error:
        st.error(error.user_message)
        return
    if text is None:
        st.warning(NOT_KEPT)
        return
    _mount(PANE_COMPONENT)(
        key=f"pane_{citation.number}",
        data={"html": document_html(text, citation)},
    )


def _mount(name: str) -> Any:
    """Declared by `declare_components()`, which every run of the page starts with.
    Falling back to declaring here would hide a run that never did."""
    return _mounts[name]


def _opening(key: str) -> Any:
    def clicked() -> None:
        state = st.session_state.get(key)
        number = getattr(state, CLICKED, None)
        if number is not None:
            st.session_state[OPEN_CITATION] = int(number)

    return clicked
