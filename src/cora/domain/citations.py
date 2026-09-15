"""How a passage becomes a `[n]` the reader can click, and open.

A citation is handed out once and keeps its number for the life of the conversation, so
a number the user has seen never moves to another passage.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from cora.domain.prose import counted, listed
from cora.ports.retrieval import RetrievedChunk

NO_MATCHES = "No matching documents."
CITATION_RUN = re.compile(r"(?<![\w\]])(?:\[\d+\])+")
"""What counts as a citation in written text, for everyone who has to agree: a run of
brackets that does not continue a word or another bracket. The renderer draws buttons by
this rule and `cited_numbers` resolves by it, so a citation the reader can click and a
citation the answer rests on are the same thing by construction."""


@dataclass(frozen=True)
class Nothing:
    """What came back when nothing came back, worded twice.

    `told` is what the model reads, `shown` names the step in the trace the user reads.
    One sentence cannot do both — the model is being told about the user, the user is
    being told about cora.
    """

    told: str
    shown: str


NOTHING_FOUND = Nothing(told=NO_MATCHES, shown=NO_MATCHES)


@dataclass(frozen=True)
class Citation:
    """One passage of one document, numbered.

    The span is where the passage sits in the cleaned text of `upload` — the document as
    it arrived that time — so `[n]` can be opened and read rather than merely named: two
    passages of one document are two citations, and a number the user has been shown
    never moves to another passage, not even when the same filename is uploaded again
    with other text in it.

    `document` is the name to show; `upload` is what to read, and `scope` is the field
    whose directory it is kept under — a passage is opened where it was ingested.
    """

    number: int
    document: str
    start: int
    end: int
    upload: str = ""
    scope: str = ""


@dataclass(frozen=True)
class Context:
    """A block of numbered passages for the model, and the citations it hands out.

    `citations` are only the ones this block added: a passage the conversation has
    already cited keeps the number it was given then.
    """

    text: str
    citations: tuple[Citation, ...]


def cited_numbers(text: str) -> tuple[int, ...]:
    """The numbers an answer cites, in the order it first cites them, each once."""
    runs = CITATION_RUN.findall(text)
    found = (int(number) for run in runs for number in re.findall(r"\d+", run))
    return tuple(dict.fromkeys(found))


def cited(text: str, citations: tuple[Citation, ...]) -> tuple[Citation, ...]:
    """The citations an answer actually cites, in number order.

    A number the answer cites that nothing was handed out for is dropped: the model
    inventing `[9]` must not put a ninth source under the answer.
    """
    by_number = {citation.number: citation for citation in citations}
    found = (by_number[n] for n in cited_numbers(text) if n in by_number)
    return tuple(sorted(found, key=lambda citation: citation.number))


def build_context_block(
    hits: list[RetrievedChunk],
    known: tuple[Citation, ...] = (),
    nothing: Nothing = NOTHING_FOUND,
) -> Context:
    """Number these passages for the model, continuing from the ones already handed out.

    Args:
        hits: The passages to write into the block, in the order they came back.
        known: Citations this conversation has already handed out. A passage among them
            is written under the number it already has, so a number the user has seen
            keeps pointing where it pointed.
        nothing: What an empty result means here, worded for the model and for the
            trace.

    Returns:
        The block as the model reads it, and the citations this block added — never the
        ones it reused.
    """
    if not hits:
        return Context(text=nothing.told, citations=())
    number_of = {_span(citation): citation.number for citation in known}
    next_number = max((citation.number for citation in known), default=0) + 1
    added: list[Citation] = []
    for hit in hits:
        span = _hit_span(hit)
        if span in number_of:
            continue
        number_of[span] = next_number
        scope, upload, document, start, end = span
        added.append(
            Citation(
                number=next_number,
                document=document,
                start=start,
                end=end,
                upload=upload,
                scope=scope,
            )
        )
        next_number += 1
    body = "\n".join(
        f"[{number_of[_hit_span(hit)]}] {hit.chunk.source}: {hit.chunk.text}"
        for hit in hits
    )
    return Context(text=body, citations=tuple(added))


def _span(citation: Citation) -> tuple[str, str, str, int, int]:
    return (
        citation.scope,
        citation.upload,
        citation.document,
        citation.start,
        citation.end,
    )


def _hit_span(hit: RetrievedChunk) -> tuple[str, str, str, int, int]:
    chunk = hit.chunk
    return (
        chunk.scope,
        chunk.upload,
        chunk.source,
        chunk.offset,
        chunk.offset + len(chunk.text),
    )


class Citable(ABC):
    """A tool payload that cites its own material.

    It takes the citations already handed out, renders itself as a numbered block, and
    says in one line what it found. Declared by inheritance, not by shape — a plugin
    payload with a `register` of its own is not citable.
    """

    @abstractmethod
    def register(self, known: tuple[Citation, ...]) -> Context:
        """Render this payload as a numbered block, continuing from `known`."""
        ...

    @abstractmethod
    def unnumbered(self) -> str:
        """This material for a reader that hands out no numbers, its source named.

        A delegated loop reads what a search found but cites nothing, so it is shown
        `document: text` rather than a numbered block — and taking cora's numbers off
        the block afterwards would take the user's own numbering with them.
        """
        ...

    @property
    @abstractmethod
    def summary(self) -> str:
        """The one line the trace shows for what was found."""
        ...


@dataclass(frozen=True)
class CitableHits(Citable):
    """Retrieved passages, citable — what a document search hands back."""

    hits: list[RetrievedChunk]
    nothing: Nothing = field(default=NOTHING_FOUND)
    """What an empty result means *here*: a search of a store nothing was uploaded to
    says something a search that merely matched nothing does not."""

    def register(self, known: tuple[Citation, ...]) -> Context:
        """The hits as a numbered block, or this search's own word for nothing."""
        return build_context_block(self.hits, known, self.nothing)

    def unnumbered(self) -> str:
        """The hits by document, as they were written, or the word for nothing."""
        if not self.hits:
            return self.nothing.told
        return "\n".join(f"{hit.chunk.source}: {hit.chunk.text}" for hit in self.hits)

    @property
    def summary(self) -> str:
        """How many passages, from which documents — each document named once."""
        if not self.hits:
            return self.nothing.shown
        sources = dict.fromkeys(hit.chunk.source for hit in self.hits)
        return f"{counted(len(self.hits), 'passage')} from {listed(list(sources))}"
