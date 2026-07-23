import dataclasses

import pytest

from core.plugin import ToolCall, ToolResult
from fakes import add_tool
from fixture_plugins import make_plugin


def test_tools_are_equal_by_value() -> None:
    assert add_tool() == add_tool()


def test_tools_differ_when_any_field_differs() -> None:
    assert add_tool() != dataclasses.replace(add_tool(), name="sum")


def test_tool_is_immutable() -> None:
    tool = add_tool()

    with pytest.raises(dataclasses.FrozenInstanceError):
        tool.name = "changed"  # ty: ignore[invalid-assignment]


def test_tool_calls_are_equal_by_value() -> None:
    a = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")
    b = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")

    assert a == b


def test_tool_call_is_immutable() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        call.call_id = "changed"  # ty: ignore[invalid-assignment]


def test_ok_result_carries_payload_and_no_error() -> None:
    result = ToolResult(call_id="call-1", payload=3)

    assert result.payload == 3
    assert result.error is None


def test_error_result_carries_error_and_no_payload() -> None:
    result = ToolResult(call_id="call-1", error="unknown tool 'nope'")

    assert result.error == "unknown tool 'nope'"
    assert result.payload is None


def test_result_with_both_payload_and_error_is_rejected() -> None:
    with pytest.raises(ValueError):
        ToolResult(call_id="call-1", payload=3, error="boom")


def test_result_with_neither_payload_nor_error_is_rejected() -> None:
    with pytest.raises(ValueError):
        ToolResult(call_id="call-1")


def test_tool_result_is_immutable() -> None:
    result = ToolResult(call_id="call-1", payload=3)

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.payload = 4  # ty: ignore[invalid-assignment]


def test_plugin_seed_docs_default_to_empty() -> None:
    assert make_plugin().seed_docs == ()


def test_plugin_carries_seed_docs_as_filename_bytes_pairs() -> None:
    plugin = make_plugin(seed_docs=(("tables.md", b"# Times tables"),))

    assert plugin.seed_docs == (("tables.md", b"# Times tables"),)


def test_plugin_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        make_plugin().system_prompt = "changed"  # ty: ignore[invalid-assignment]
