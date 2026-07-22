from docchat.plugin import Tool, ToolCall
from docchat.tool_runtime import ToolRuntime


def add(a: int, b: int) -> int:
    return a + b


ADD_TOOL = Tool(
    name="add",
    description="Add two integers.",
    parameter_schema={
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    },
    run=add,
)


def test_valid_call_runs_the_tool_and_returns_ok_result() -> None:
    runtime = ToolRuntime(tools=(ADD_TOOL,))

    result = runtime.execute(
        ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")
    )

    assert result.call_id == "call-1"
    assert result.payload == 3
    assert result.error is None
