import pytest

from docchat.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from docchat.ingestion import ingest
from docchat.loaders import LOADERS
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
