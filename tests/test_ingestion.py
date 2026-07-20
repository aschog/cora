import pytest

from docchat.errors import FileTooLargeError, UnsupportedFileTypeError
from docchat.ingestion import ingest
from docchat.loaders import LOADERS


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
