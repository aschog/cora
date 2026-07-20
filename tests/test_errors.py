import pytest

from docchat.errors import (
    DocChatError,
    EmptyDocumentError,
    FileTooLargeError,
    IngestionError,
    UnreadableFileError,
    UnsupportedFileTypeError,
)


def test_base_error_exposes_user_presentable_message() -> None:
    error = DocChatError("Something went wrong. Please try again.")

    assert error.user_message == "Something went wrong. Please try again."


INGESTION_ERRORS = [
    UnsupportedFileTypeError,
    FileTooLargeError,
    EmptyDocumentError,
    UnreadableFileError,
]


@pytest.mark.parametrize("error_type", INGESTION_ERRORS)
def test_ingestion_error_is_a_docchat_error(error_type: type[DocChatError]) -> None:
    assert issubclass(error_type, DocChatError)


@pytest.mark.parametrize("error_type", INGESTION_ERRORS)
def test_ingestion_error_message_names_the_offending_file(
    error_type: type[IngestionError],
) -> None:
    error = error_type("budget.xlsx")

    assert "budget.xlsx" in error.user_message
    assert error.filename == "budget.xlsx"
