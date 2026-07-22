import dataclasses

import pytest

from docchat.plugin import Tool


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
