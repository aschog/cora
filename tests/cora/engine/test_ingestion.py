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
    ingested = ingest(b"  Spaced   out\n\n\n\nparagraph.  ", "notes.txt", LOADERS)

    assert ingested.text == clean_text(
        LOADERS[".txt"](b"  Spaced   out\n\n\n\nparagraph.  ", "notes.txt")
    )
    assert ingested.chunks[0].text in ingested.text


def test_runs_of_blank_lines_collapse_to_one_paragraph_break() -> None:
    assert clean_text("a\n\n\n\nb") == "a\n\nb"
