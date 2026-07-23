from core.plugin import Tool, ToolCall
from core.tool_runtime import ToolRuntime
from fakes import add_tool


def explode() -> None:
    raise RuntimeError("boom")


EXPLODING_TOOL = Tool(
    name="explode",
    description="Always fails.",
    parameter_schema={"type": "object", "properties": {}},
    run=explode,
)


def make_runtime() -> ToolRuntime:
    return ToolRuntime(tools=(add_tool(), EXPLODING_TOOL))


def test_valid_call_runs_the_tool_and_returns_ok_result() -> None:
    result = make_runtime().execute(
        ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")
    )

    assert result.call_id == "call-1"
    assert result.payload == 3
    assert result.error is None


def test_wrong_argument_type_yields_error_result_naming_the_problem() -> None:
    result = make_runtime().execute(
        ToolCall(name="add", arguments={"a": "one", "b": 2}, call_id="call-2")
    )

    assert result.call_id == "call-2"
    assert result.payload is None
    assert result.error is not None
    assert "integer" in result.error


def silent() -> None:
    return None


SILENT_TOOL = Tool(
    name="silent",
    description="Returns nothing.",
    parameter_schema={"type": "object", "properties": {}},
    run=silent,
)


def test_tool_returning_none_yields_error_result() -> None:
    runtime = ToolRuntime(tools=(SILENT_TOOL,))

    result = runtime.execute(ToolCall(name="silent", arguments={}, call_id="call-6"))

    assert result.call_id == "call-6"
    assert result.payload is None
    assert result.error is not None
    assert "silent" in result.error


def test_raising_tool_yields_error_result_instead_of_crashing() -> None:
    result = make_runtime().execute(
        ToolCall(name="explode", arguments={}, call_id="call-5")
    )

    assert result.call_id == "call-5"
    assert result.payload is None
    assert result.error is not None
    assert "explode" in result.error


def test_unknown_tool_name_yields_error_result() -> None:
    result = make_runtime().execute(
        ToolCall(name="subtract", arguments={"a": 1, "b": 2}, call_id="call-4")
    )

    assert result.call_id == "call-4"
    assert result.payload is None
    assert result.error is not None
    assert "subtract" in result.error


def test_missing_required_argument_yields_error_result_naming_the_problem() -> None:
    result = make_runtime().execute(
        ToolCall(name="add", arguments={"a": 1}, call_id="call-3")
    )

    assert result.payload is None
    assert result.error is not None
    assert "b" in result.error
