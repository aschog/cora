import pytest

from core.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from core.ingestion import ingest
from core.loaders import LOADERS
from pdf_fixtures import make_pdf_bytes


def test_unsupported_extension_lists_supported_formats() -> None:
    with pytest.raises(UnsupportedFileTypeError) as excinfo:
        ingest(b"data", "spreadsheet.xlsx")

    message = excinfo.value.user_message
    assert "spreadsheet.xlsx" in message
    assert all(ext in message for ext in LOADERS)


def test_extension_matching_is_case_insensitive() -> None:
    chunks = ingest(b"Some content.", "NOTES.TXT")

    assert [chunk.text for chunk in chunks] == ["Some content."]


def test_filename_without_extension_is_rejected() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        ingest(b"data", "README")


def test_oversized_file_is_rejected_before_parsing() -> None:
    undecodable_and_oversized = b"\xff\xfe" * 100

    with pytest.raises(FileTooLargeError) as excinfo:
        ingest(undecodable_and_oversized, "notes.txt", max_bytes=50)

    assert "notes.txt" in excinfo.value.user_message


def test_whitespace_only_txt_raises_empty_document_error() -> None:
    with pytest.raises(EmptyDocumentError) as excinfo:
        ingest(b"   \n\t  \n", "blank.txt")

    assert "blank.txt" in excinfo.value.user_message


def test_image_only_pdf_raises_empty_document_error() -> None:
    data = make_pdf_bytes("", "")

    with pytest.raises(EmptyDocumentError):
        ingest(data, "scanned.pdf")


def test_ingest_txt_yields_ordered_chunks_named_by_filename() -> None:
    text = "\n\n".join(f"Paragraph {n} with several words." for n in range(80))

    chunks = ingest(text.encode(), "notes.txt")

    assert len(chunks) > 1
    assert all(chunk.source == "notes.txt" for chunk in chunks)
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_ingest_pdf_end_to_end_with_provenance() -> None:
    data = make_pdf_bytes("First page content.", "Second page content.")

    chunks = ingest(data, "doc.pdf")

    assert chunks
    assert all(chunk.source == "doc.pdf" for chunk in chunks)
    combined = " ".join(chunk.text for chunk in chunks)
    assert "First page content." in combined
    assert "Second page content." in combined
