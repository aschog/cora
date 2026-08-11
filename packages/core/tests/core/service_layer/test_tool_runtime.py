import pytest

from cora.core.domain.errors import RetrievalError
from cora.core.ports.plugin import Tool, ToolCall, ToolRefusal
from cora.core.service_layer.tool_runtime import ToolRuntime
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
    assert "RuntimeError" in result.error


def test_a_refusal_says_why_in_the_tools_own_words() -> None:
    def refuse() -> None:
        raise ToolRefusal("a calorie target that low leaves no room for carbs")

    refusing = Tool(
        name="plan",
        description="Refuses impossible input.",
        parameter_schema={"type": "object", "properties": {}},
        run=refuse,
    )

    result = ToolRuntime(tools=(refusing,)).execute(
        ToolCall(name="plan", arguments={}, call_id="call-8")
    )

    assert (
        result.error
        == "tool 'plan' failed: a calorie target that low leaves no room for carbs"
    )


def test_an_accidental_value_error_is_still_only_a_kind() -> None:
    """A refusal is declared, not guessed from a type: `ValueError` is what a
    library raises by accident as readily as a tool raises it on purpose."""

    def slip() -> None:
        int("https://api.example.com/v1?key=sk-live-secret")

    slipping = Tool(
        name="slip",
        description="Fails inside a library.",
        parameter_schema={"type": "object", "properties": {}},
        run=slip,
    )

    result = ToolRuntime(tools=(slipping,)).execute(
        ToolCall(name="slip", arguments={}, call_id="call-9")
    )

    assert result.error is not None
    assert "sk-live-secret" not in result.error
    assert "ValueError" in result.error


def test_a_tools_own_exception_text_is_never_passed_on() -> None:
    """An exception that merely escaped can carry anything the tool was holding —
    a URL with a key in it — so only its kind travels on."""

    def leak() -> None:
        raise RuntimeError("401 for https://api.example.com/v1?key=sk-live-secret")

    leaking = Tool(
        name="leak",
        description="Fails with a secret in the message.",
        parameter_schema={"type": "object", "properties": {}},
        run=leak,
    )

    result = ToolRuntime(tools=(leaking,)).execute(
        ToolCall(name="leak", arguments={}, call_id="call-7")
    )

    assert result.error is not None
    assert "sk-live-secret" not in result.error


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


def unavailable() -> None:
    raise RetrievalError


UNAVAILABLE_TOOL = Tool(
    name="unavailable",
    description="Fails because its infrastructure is down.",
    parameter_schema={"type": "object", "properties": {}},
    run=unavailable,
)


def test_an_adapter_error_from_a_tool_propagates_instead_of_becoming_a_result() -> None:
    runtime = ToolRuntime(tools=(UNAVAILABLE_TOOL,))

    with pytest.raises(RetrievalError):
        runtime.execute(ToolCall(name="unavailable", arguments={}, call_id="call-7"))
