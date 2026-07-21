from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned from a similarity search: its provenance plus a score.

    ``score`` is a relevance score where higher means more relevant, on the
    convention shared by the retriever port and its adapters. The provenance
    fields mirror :class:`docchat.chunk.Chunk`.
    """

    text: str
    source: str
    index: int
    offset: int
    score: float
