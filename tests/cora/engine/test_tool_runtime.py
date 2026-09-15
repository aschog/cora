import pytest

from cora.domain.errors import RetrievalError
from cora.engine.host import PluginHost
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.plugin import Tool, ToolCall
from fakes import (
    TEXT_LOADERS,
    FakeDocuments,
    FakeEmbedder,
    FakeRetriever,
    add_tool,
    host_for,
)


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


FITNESS, TRAVEL = "fitness", "travel"
PLAN = b"The block holds intensity and drops volume in the fourth week."
KYOTO = b"The sleeper to Kyoto sells out a month before the maples turn."


def _two_fields() -> KnowledgeBase:
    kb = KnowledgeBase(
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        loaders=TEXT_LOADERS,
        documents=FakeDocuments(),
    )
    kb.add_file(PLAN, "plan.md", FITNESS)
    kb.add_file(KYOTO, "kyoto.md", TRAVEL)
    return kb


def _reading(host: PluginHost) -> Tool:
    def read() -> str:
        return " ".join(hit.chunk.source for hit in host.documents.search("notes", 5))

    return Tool(
        name="read",
        description="Reads the documents.",
        parameter_schema={"type": "object", "properties": {}},
        run=read,
    )


def test_a_plugins_own_search_reads_the_field_the_turn_is_running_in() -> None:
    """A plugin cannot see the turn it is running in, so the field reaches its search
    through the call rather than through an argument it would have to fill."""
    host = host_for(documents=_two_fields())
    runtime = ToolRuntime(tools=(_reading(host),))

    result = runtime.execute(
        ToolCall(name="read", arguments={}, call_id="c1"), frozenset({TRAVEL})
    )

    assert result.payload == "kyoto.md"
