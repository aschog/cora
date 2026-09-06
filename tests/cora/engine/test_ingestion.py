"""What ingestion decides, against loaders of the test's own making. Which formats a
deployment reads is the adapters' business, so the real registry is exercised where it
lives — `tests/cora/adapters/test_loaders.py`, and the PDF path end to end
beside it.
"""

import pytest

from cora.domain.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from cora.engine.ingestion import clean_text, ingest
from cora.ports.loading import Loaders


def _text(data: bytes, filename: str) -> str:
    return data.decode("utf-8")


LOADERS: Loaders = {".txt": _text, ".md": _text}


def test_unsupported_extension_lists_supported_formats() -> None:
    with pytest.raises(UnsupportedFileTypeError) as excinfo:
        ingest(b"data", "spreadsheet.xlsx", LOADERS)

    message = excinfo.value.user_message
    assert "spreadsheet.xlsx" in message
    assert all(ext in message for ext in LOADERS)


def test_the_formats_offered_are_the_ones_it_was_given() -> None:
    """Nothing in core decides what can be read: a registry without `.md` rejects it,
    and one with a format core has never heard of accepts it."""
    with pytest.raises(UnsupportedFileTypeError):
        ingest(b"# Title", "notes.md", {".txt": _text})

    chunks = ingest(b"body", "page.rst", {".rst": _text}).chunks

    assert [chunk.text for chunk in chunks] == ["body"]


def test_extension_matching_is_case_insensitive() -> None:
    chunks = ingest(b"Some content.", "NOTES.TXT", LOADERS).chunks

    assert [chunk.text for chunk in chunks] == ["Some content."]


def test_filename_without_extension_is_rejected() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        ingest(b"data", "README", LOADERS)


def test_oversized_file_is_rejected_before_parsing() -> None:
    undecodable_and_oversized = b"\xff\xfe" * 100

    with pytest.raises(FileTooLargeError) as excinfo:
        ingest(undecodable_and_oversized, "notes.txt", LOADERS, max_bytes=50)

    assert "notes.txt" in excinfo.value.user_message


def test_whitespace_only_document_raises_empty_document_error() -> None:
    with pytest.raises(EmptyDocumentError) as excinfo:
        ingest(b"   \n\t  \n", "blank.txt", LOADERS)

    assert "blank.txt" in excinfo.value.user_message


def test_ingest_yields_ordered_chunks_named_by_filename() -> None:
    text = "\n\n".join(f"Paragraph {n} with several words." for n in range(80))

    chunks = ingest(text.encode(), "notes.txt", LOADERS).chunks

    assert len(chunks) > 1
    assert all(chunk.source == "notes.txt" for chunk in chunks)
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_ingest_hands_back_the_cleaned_text_the_chunks_came_from() -> None:
    """The text is what a citation's offsets point into, so it has to be the cleaned
    text — the bytes that arrived are not what was chunked."""
    ingested = ingest(b"  Spaced   out\n\n\n\nparagraph.  ", "notes.txt", LOADERS)

    assert ingested.text == clean_text(
        LOADERS[".txt"](b"  Spaced   out\n\n\n\nparagraph.  ", "notes.txt")
    )
    assert ingested.chunks[0].text in ingested.text


def test_crlf_becomes_lf() -> None:
    assert clean_text("a\r\nb\r\nc") == "a\nb\nc"


def test_lone_cr_becomes_lf() -> None:
    assert clean_text("a\rb") == "a\nb"


def test_surrounding_whitespace_is_trimmed() -> None:
    assert clean_text("  \n hello \n  ") == "hello"


def test_runs_of_blank_lines_collapse_to_one_paragraph_break() -> None:
    assert clean_text("a\n\n\n\nb") == "a\n\nb"


def test_ordinary_paragraph_break_is_preserved() -> None:
    assert clean_text("a\n\nb") == "a\n\nb"
