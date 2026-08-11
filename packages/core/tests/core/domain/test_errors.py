import pytest

from cora.core.domain.errors import (
    AdapterError,
    CoreError,
    EmbeddingError,
    EmptyDocumentError,
    FileTooLargeError,
    IngestionError,
    InputRejectedError,
    LlmError,
    PluginLoadError,
    RetrievalError,
    ToolLoopLimitError,
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
def test_ingestion_error_is_a_core_error(error_type: type[CoreError]) -> None:
    assert issubclass(error_type, CoreError)


@pytest.mark.parametrize("error_type", INGESTION_ERRORS)
def test_ingestion_error_message_names_the_offending_file(
    error_type: type[IngestionError],
) -> None:
    error = error_type("budget.xlsx")

    assert "budget.xlsx" in error.user_message
    assert error.filename == "budget.xlsx"


ADAPTER_ERRORS = [EmbeddingError, RetrievalError, LlmError]


@pytest.mark.parametrize("error_type", ADAPTER_ERRORS)
def test_adapter_error_is_a_core_error(error_type: type[AdapterError]) -> None:
    assert issubclass(error_type, CoreError)


@pytest.mark.parametrize("error_type", ADAPTER_ERRORS)
def test_adapter_error_carries_a_user_message(
    error_type: type[AdapterError],
) -> None:
    assert error_type().user_message


def test_plugin_load_error_names_plugin_and_reason() -> None:
    error = PluginLoadError("fitness", "the plugin module could not be imported")

    assert issubclass(PluginLoadError, CoreError)
    assert "fitness" in error.user_message
    assert "could not be imported" in error.user_message


def test_tool_loop_limit_error_carries_a_friendly_message() -> None:
    error = ToolLoopLimitError()

    assert issubclass(ToolLoopLimitError, CoreError)
    assert error.user_message


def test_input_rejection_carries_the_rule_supplied_message() -> None:
    error = InputRejectedError("Please ask a health professional about medication.")

    assert issubclass(InputRejectedError, CoreError)
    assert error.user_message == "Please ask a health professional about medication."
