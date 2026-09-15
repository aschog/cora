"""How a document is cut into the passages the index holds."""

from cora.domain.chunk import Chunk

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 150

# Coarsest to finest boundary; "" is the hard character-level fallback.
_SEPARATORS = ["\n\n", "\n", " ", ""]


def chunk_text(
    text: str,
    *,
    source: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Cut text into chunks that can be read back out of it exactly.

    Every chunk is a substring of `text` and carries the offset it starts at, so a
    citation into one is a span of the document the user can be shown.

    Args:
        text: The cleaned text, which is what an offset is measured in.
        source: The filename to stamp on each chunk.
        chunk_size: Characters, not tokens — the largest a chunk may be.
        overlap: Characters each chunk after the first reaches back by, so a sentence
            cut in two is whole in one of them.

    Returns:
        The chunks in reading order, or none at all for text that is only whitespace.

    Raises:
        ValueError: `chunk_size` is not positive, or `overlap` does not fit inside it.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    if not text.strip():
        return []

    spans = _split(text, 0, chunk_size - overlap, _SEPARATORS)
    return _to_chunks(spans, text, source, overlap)


def _split(
    text: str, base: int, chunk_size: int, separators: list[str]
) -> list[tuple[int, int]]:
    if len(text) <= chunk_size:
        return [(base, base + len(text))]

    separator, *finer = separators
    if separator == "":
        return [
            (base + i, base + min(i + chunk_size, len(text)))
            for i in range(0, len(text), chunk_size)
        ]

    spans: list[tuple[int, int]] = []
    start: int | None = None
    end = 0
    for fragment, offset in _fragments(text, separator):
        frag_end = offset + len(fragment)
        if start is not None and frag_end - start <= chunk_size:
            end = frag_end
            continue
        if start is not None:
            spans.append((base + start, base + end))
        if len(fragment) > chunk_size:
            spans.extend(_split(fragment, base + offset, chunk_size, finer))
            start = None
        else:
            start, end = offset, frag_end
    if start is not None:
        spans.append((base + start, base + end))
    return spans


def _fragments(text: str, separator: str) -> list[tuple[str, int]]:
    fragments: list[tuple[str, int]] = []
    offset = 0
    for fragment in text.split(separator):
        if fragment:
            fragments.append((fragment, offset))
        offset += len(fragment) + len(separator)
    return fragments


def _to_chunks(
    spans: list[tuple[int, int]], text: str, source: str, overlap: int
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for index, (base_offset, end) in enumerate(spans):
        start = max(0, base_offset - overlap) if index else base_offset
        chunks.append(
            Chunk(text=text[start:end], source=source, index=index, offset=start)
        )
    return chunks
