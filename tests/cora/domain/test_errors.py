import pytest

from cora.domain.errors import (
    CoreError,
    EmptyDocumentError,
    FileTooLargeError,
    IngestionError,
    PluginLoadError,
    UnreadableFileError,
    UnsupportedFileTypeError,
)


def test_base_error_exposes_user_presentable_message() -> None:
    error = CoreError("Something went wrong. Please try again.")

    assert error.user_message == "Something went wrong. Please try again."


INGESTION_ERRORS = [
    UnsupportedFileTypeError,
    FileTooLargeError,
    EmptyDocumentError,
    UnreadableFileError,
]


@pytest.mark.parametrize("error_type", INGESTION_ERRORS)
def test_ingestion_error_message_names_the_offending_file(
    error_type: type[IngestionError],
) -> None:
    error = error_type("budget.xlsx")

    assert "budget.xlsx" in error.user_message


def test_plugin_load_error_names_plugin_and_reason() -> None:
    error = PluginLoadError("fitness", "the plugin module could not be imported")

    assert issubclass(PluginLoadError, CoreError)
    assert "fitness" in error.user_message
    assert "could not be imported" in error.user_message


def test_an_error_names_no_step_until_a_step_is_named() -> None:
    assert CoreError("Something went wrong. Please try again.").step == ""
