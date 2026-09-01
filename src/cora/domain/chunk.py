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
        """Measure the length of every chunk that has text to measure.

        A chunk read back from the index has the length and not the text; one cut from a
        document has the text, and its length is what the text is — taken here rather
        than passed in, so the two can never be given disagreeing values.
        """
        if self.text:
            object.__setattr__(self, "length", len(self.text))
