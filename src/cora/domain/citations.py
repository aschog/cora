import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import NamedTuple

from cora.domain.prose import counted, listed
from cora.ports.retrieval import RetrievedChunk

NO_MATCHES = "No matching documents."


class Nothing(NamedTuple):
    """What came back when nothing came back, worded twice: `told` is what the model
    reads, `shown` names the step in the trace the user reads. One sentence cannot do
    both — the model is being told about the user, the user is being told about cora."""

    told: str
    shown: str


NOTHING_FOUND = Nothing(told=NO_MATCHES, shown=NO_MATCHES)


@dataclass(frozen=True)
class Citation:
    """One passage of one document, numbered. The span is where the passage sits in the
    document's cleaned text, so `[n]` can be opened and read rather than merely named:
    two passages of one document are two citations, and a number the user has been shown
    never moves to another passage."""

    number: int
    document: str
    start: int
    end: int


@dataclass(frozen=True)
class Context:
    text: str
    citations: tuple[Citation, ...]


def cited_numbers(text: str) -> tuple[int, ...]:
    runs = re.findall(r"(?<![\w\]])(?:\[\d+\])+", text)
    found = (int(number) for run in runs for number in re.findall(r"\d+", run))
    return tuple(dict.fromkeys(found))


def cited(text: str, citations: tuple[Citation, ...]) -> tuple[Citation, ...]:
    by_number = {citation.number: citation for citation in citations}
    found = (by_number[n] for n in cited_numbers(text) if n in by_number)
    return tuple(sorted(found, key=lambda citation: citation.number))


def build_context_block(
    hits: list[RetrievedChunk],
    known: tuple[Citation, ...] = (),
    nothing: Nothing = NOTHING_FOUND,
) -> Context:
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
        added.append(Citation(next_number, *span))
        next_number += 1
    body = "\n".join(
        f"[{number_of[_hit_span(hit)]}] {hit.chunk.source}: {hit.chunk.text}"
        for hit in hits
    )
    return Context(text=body, citations=tuple(added))


def _span(citation: Citation) -> tuple[str, int, int]:
    return (citation.document, citation.start, citation.end)


def _hit_span(hit: RetrievedChunk) -> tuple[str, int, int]:
    chunk = hit.chunk
    return (chunk.source, chunk.offset, chunk.offset + len(chunk.text))


class Citable(ABC):
    """A tool payload that cites its own material: it takes the citations already
    handed out, renders itself as a numbered block, and says in one line what it
    found. Declared by inheritance, not by shape — a plugin payload with a
    `register` of its own is not citable.
    """

    @abstractmethod
    def register(self, known: tuple[Citation, ...]) -> Context: ...

    @property
    @abstractmethod
    def summary(self) -> str: ...


@dataclass(frozen=True)
class CitableHits(Citable):
    hits: list[RetrievedChunk]
    nothing: Nothing = field(default=NOTHING_FOUND)
    """What an empty result means *here*: a search of a store nothing was uploaded to
    says something a search that merely matched nothing does not."""

    def register(self, known: tuple[Citation, ...]) -> Context:
        return build_context_block(self.hits, known, self.nothing)

    @property
    def summary(self) -> str:
        if not self.hits:
            return self.nothing.shown
        sources = dict.fromkeys(hit.chunk.source for hit in self.hits)
        return f"{counted(len(self.hits), 'passage')} from {listed(list(sources))}"
