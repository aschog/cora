import dataclasses

import pytest

from cora.ports.plugin import ToolCall, ToolResult
from fakes import add_tool
from fixture_plugins import make_plugin


def test_tools_are_equal_by_value() -> None:
    assert add_tool() == add_tool()


def test_tools_differ_when_any_field_differs() -> None:
    assert add_tool() != dataclasses.replace(add_tool(), name="sum")


def test_tool_calls_are_equal_by_value() -> None:
    a = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")
    b = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")

    assert a == b


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


def test_render_returns_the_error_message() -> None:
    assert ToolResult(call_id="c1", error="Unknown tool 'tdee'.").render() == (
        "Unknown tool 'tdee'."
    )


def test_render_returns_a_string_payload_as_is() -> None:
    assert ToolResult(call_id="c1", payload="2500 kcal").render() == "2500 kcal"


def test_render_serialises_other_payloads_as_json() -> None:
    result = ToolResult(call_id="c1", payload={"tdee": 2500, "unit": "kcal"})

    assert result.render() == '{"tdee": 2500, "unit": "kcal"}'


def test_plugin_seed_docs_default_to_empty() -> None:
    assert make_plugin().seed_docs == ()


def test_plugin_carries_seed_docs_as_filename_bytes_pairs() -> None:
    plugin = make_plugin(seed_docs=(("tables.md", b"# Times tables"),))

    assert plugin.seed_docs == (("tables.md", b"# Times tables"),)
