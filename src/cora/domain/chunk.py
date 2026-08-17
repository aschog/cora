from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """An immutable slice of a document with its provenance.

    ``index`` is the zero-based position in the chunk sequence; ``offset`` is
    the character position of ``text`` in the cleaned source text. ``upload`` names
    which upload that text was — the same file edited and added again is another one —
    so a span cut here can be read back against the text it was measured in. It is
    empty only between chunking and indexing, where nothing has asked yet.
    """

    text: str
    source: str
    index: int
    offset: int
    upload: str = ""
