import pytest

from docchat.errors import UnsupportedFileTypeError
from docchat.ingestion import ingest
from docchat.loaders import LOADERS


def test_unsupported_extension_lists_supported_formats() -> None:
    with pytest.raises(UnsupportedFileTypeError) as excinfo:
        ingest(b"data", "spreadsheet.xlsx")

    message = excinfo.value.user_message
    assert "spreadsheet.xlsx" in message
    assert all(ext in message for ext in LOADERS)
