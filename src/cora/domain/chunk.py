"""A passage of a document, and where in that document it came from."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """An immutable slice of a document with its provenance.

    ``index`` is the zero-based position in the chunk sequence; ``offset`` is
    the character position of ``text`` in the cleaned source text, and ``length`` is how
    far it runs — the two together are the span, and they are what the index keeps, so a
    chunk read back out of one carries the span with no text in it until the file it was
    measured in is read. ``upload`` names which upload that text was — the same file
    edited and added again is another one — and ``scope`` names the field it was
    ingested into, which is the directory that file is kept under. Both are empty only
    between chunking and indexing: the index is what records them.
    """

    text: str
    source: str
    index: int
    offset: int
    upload: str = ""
    scope: str = ""
    length: int = 0

    def __post_init__(self) -> None:
        """Take the length from the text, for every chunk that was cut from one.

        A chunk read back from the index has the length and not the text, and one just
        cut has the text and no length written out beside it — measuring it here is what
        keeps the two from ever disagreeing.
        """
        if self.text and not self.length:
            object.__setattr__(self, "length", len(self.text))
