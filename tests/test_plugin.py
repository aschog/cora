import dataclasses

import pytest

from docchat.plugin import Plugin, Tool, ToolCall, ToolResult


def add(a: int, b: int) -> int:
    return a + b


ADD_SCHEMA = {
    "type": "object",
    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    "required": ["a", "b"],
}


def make_add_tool() -> Tool:
    return Tool(
        name="add",
        description="Add two integers.",
        parameter_schema=ADD_SCHEMA,
        run=add,
    )


def test_tools_are_equal_by_value() -> None:
    assert make_add_tool() == make_add_tool()


def test_tools_differ_when_any_field_differs() -> None:
    assert make_add_tool() != dataclasses.replace(make_add_tool(), name="sum")


def test_tool_is_immutable() -> None:
    tool = make_add_tool()

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
    plugin = Plugin(
        system_prompt="You are a maths tutor.",
        tools=(make_add_tool(),),
        validation_rules=(),
    )

    assert plugin.seed_docs == ()


def test_plugin_carries_seed_docs_as_filename_bytes_pairs() -> None:
    plugin = Plugin(
        system_prompt="You are a maths tutor.",
        tools=(make_add_tool(),),
        validation_rules=(),
        seed_docs=(("tables.md", b"# Times tables"),),
    )

    assert plugin.seed_docs == (("tables.md", b"# Times tables"),)


def test_plugin_is_immutable() -> None:
    plugin = Plugin(
        system_prompt="You are a maths tutor.",
        tools=(make_add_tool(),),
        validation_rules=(),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        plugin.system_prompt = "changed"  # ty: ignore[invalid-assignment]
