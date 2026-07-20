from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """An immutable slice of a document with its provenance.

    ``index`` is the zero-based position in the chunk sequence; ``offset`` is
    the character position of ``text`` in the cleaned source text.
    """

    text: str
    source: str
    index: int
    offset: int
