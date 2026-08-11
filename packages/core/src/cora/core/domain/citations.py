import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from cora.core.domain.prose import counted, listed
from cora.core.ports.retrieval import RetrievedChunk

NO_MATCHES = "No matching documents."


@dataclass(frozen=True)
class Source:
    number: int
    name: str


@dataclass(frozen=True)
class Context:
    text: str
    sources: tuple[Source, ...]


def cited_numbers(text: str) -> tuple[int, ...]:
    runs = re.findall(r"(?<![\w\]])(?:\[\d+\])+", text)
    found = (int(number) for run in runs for number in re.findall(r"\d+", run))
    return tuple(dict.fromkeys(found))


def cited_sources(text: str, sources: tuple[Source, ...]) -> tuple[Source, ...]:
    by_number = {source.number: source for source in sources}
    cited = (by_number[n] for n in cited_numbers(text) if n in by_number)
    return tuple(sorted(cited, key=lambda source: source.number))


def build_context_block(
    hits: list[RetrievedChunk], known: tuple[Source, ...] = ()
) -> Context:
    if not hits:
        return Context(text=NO_MATCHES, sources=())
    number_of = {source.name: source.number for source in known}
    fresh = [
        name
        for name in dict.fromkeys(hit.chunk.source for hit in hits)
        if name not in number_of
    ]
    start = max((source.number for source in known), default=0) + 1
    added = tuple(
        Source(number, name) for number, name in enumerate(fresh, start=start)
    )
    number_of.update({source.name: source.number for source in added})
    body = "\n".join(
        f"[{number_of[hit.chunk.source]}] {hit.chunk.source}: {hit.chunk.text}"
        for hit in hits
    )
    return Context(text=body, sources=added)


class Citable(ABC):
    """A tool payload that cites its own material: it takes the numbers already
    handed out, renders itself as a numbered block, and says in one line what it
    found. Declared by inheritance, not by shape — a plugin payload with a
    `register` of its own is not citable.
    """

    @abstractmethod
    def register(self, known: tuple[Source, ...]) -> Context: ...

    @property
    @abstractmethod
    def summary(self) -> str: ...


@dataclass(frozen=True)
class CitableHits(Citable):
    hits: list[RetrievedChunk]

    def register(self, known: tuple[Source, ...]) -> Context:
        return build_context_block(self.hits, known)

    @property
    def summary(self) -> str:
        if not self.hits:
            return NO_MATCHES
        sources = dict.fromkeys(hit.chunk.source for hit in self.hits)
        return f"{counted(len(self.hits), 'passage')} from {listed(list(sources))}"
