import re
from collections.abc import Sequence
from html import escape

from markdown_it import MarkdownIt

from cora.domain.citations import Citation
from cora.domain.trace import TraceStep

DETAIL_CAP = 800
SUMMARY_CAP = 200
CITATION_ANCHOR = "citation-{number}"
_CITE_BUTTON = (
    '<button type="button" class="cite" data-cite="{number}">[{number}]</button>'
)
_RUN = re.compile(r"(?<![\w\]])(?:\[\d+\])+")
_NUMBER = re.compile(r"\[(\d+)\]")
_CODE = re.compile(r"<(pre|code)\b.*?</\1>", re.DOTALL)
_TAG = re.compile(r"<[^>]*>")
_MARKDOWN = MarkdownIt("commonmark", {"html": False}).disable("image")
"""Rendering with HTML disabled and images with it, because the answer is written by a
model reading the user's documents: a document that asks for a script gets escaped text,
and one that asks for an image gets no outbound fetch from the reader's browser."""


def step_text(step: TraceStep) -> str:
    """The whole step as plain text, because the caller renders it as code: a
    summary names the tool the model asked for, and a document can tell it what
    to ask for, so nothing here may be markdown."""
    head = _capped(" ".join(step.summary.split()), SUMMARY_CAP)
    if step.failed:
        head = f"⚠️ {head}"
    if not step.detail or step.detail in step.summary:
        return head
    return f"{head}\n{_capped(step.detail, DETAIL_CAP)}"


def _capped(text: str, cap: int) -> str:
    return text if len(text) <= cap else f"{text[:cap]}…"


def numbered_citations(citations: Sequence[Citation]) -> list[str]:
    """One line per cited passage, not per document: two passages of one document are
    two citations, and the panel is what says which number opens which."""
    return [f"[{citation.number}] {citation.document}" for citation in citations]


def answer_html(answer: str, citations: Sequence[Citation]) -> str:
    """The answer as markdown, with every `[n]` that resolves turned into a button the
    reader can press. A number nothing was registered under stays the text the model
    wrote, and one inside code stays code — an example of indexing a list is not a
    citation."""
    numbers = {citation.number for citation in citations}
    rendered = _MARKDOWN.render(answer)
    written: list[str] = []
    read = 0
    for code in _CODE.finditer(rendered):
        written.append(_linked(rendered[read : code.start()], numbers))
        written.append(code.group(0))
        read = code.end()
    written.append(_linked(rendered[read:], numbers))
    return "".join(written)


def document_html(text: str, citation: Citation | None) -> str:
    """The document as text, never as markup, with the cited span marked so the pane
    can scroll to it. A span reaching past the end marks what is there: the offsets
    were taken at ingest, and the file may have been re-uploaded shorter since."""
    if citation is None:
        return escape(text)
    start = min(max(citation.start, 0), len(text))
    end = min(max(citation.end, start), len(text))
    anchor = CITATION_ANCHOR.format(number=citation.number)
    return (
        f"{escape(text[:start])}"
        f'<mark id="{anchor}">{escape(text[start:end])}</mark>'
        f"{escape(text[end:])}"
    )


def _linked(html: str, numbers: set[int]) -> str:
    """Buttons in the text of rendered HTML, never in a tag: `[1]` in an image's alt
    text is not a citation, and substituting there would break the attribute open."""
    written: list[str] = []
    read = 0
    for tag in _TAG.finditer(html):
        written.append(_buttons(html[read : tag.start()], numbers))
        written.append(tag.group(0))
        read = tag.end()
    written.append(_buttons(html[read:], numbers))
    return "".join(written)


def _buttons(text: str, numbers: set[int]) -> str:
    """A run of numbers — `[1][2]` — is as many citations as it has brackets, which is
    the rule `cited_numbers` reads by. Each number resolves on its own."""

    def run(found: re.Match[str]) -> str:
        return _NUMBER.sub(_button(numbers), found.group(0))

    return _RUN.sub(run, text)


def _button(numbers: set[int]):
    def one(found: re.Match[str]) -> str:
        number = int(found.group(1))
        if number not in numbers:
            return found.group(0)
        return _CITE_BUTTON.format(number=number)

    return one


def ingest_message(filename: str, chunks: int) -> str:
    if not chunks:
        return f"{filename} is already in your knowledge base."
    unit = "chunk" if chunks == 1 else "chunks"
    return f"Added {filename} — {chunks} {unit}."
