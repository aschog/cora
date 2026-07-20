from docchat.chunk import Chunk

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
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    if not text.strip():
        return []

    pieces = _split(text, chunk_size, _SEPARATORS)
    return _locate(pieces, text, source)


def _split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Recursively split text into pieces no larger than chunk_size.

    Packs adjacent fragments greedily at the coarsest separator that fits;
    any fragment still too large is recursively split at the next finer one.
    """
    if len(text) <= chunk_size:
        return [text]

    separator, *finer = separators
    if separator == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    fragments = [f for f in text.split(separator) if f]
    pieces: list[str] = []
    current = ""
    for fragment in fragments:
        candidate = f"{current}{separator}{fragment}" if current else fragment
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            pieces.append(current)
        if len(fragment) > chunk_size:
            pieces.extend(_split(fragment, chunk_size, finer))
            current = ""
        else:
            current = fragment
    if current:
        pieces.append(current)
    return pieces


def _locate(pieces: list[str], text: str, source: str) -> list[Chunk]:
    """Attach provenance by finding each piece's position in the source text."""
    chunks: list[Chunk] = []
    cursor = 0
    for index, piece in enumerate(pieces):
        offset = text.find(piece, cursor)
        chunks.append(Chunk(text=piece, source=source, index=index, offset=offset))
        cursor = offset + len(piece)
    return chunks
