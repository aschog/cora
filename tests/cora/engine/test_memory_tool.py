import pytest

from cora.domain.errors import MemoryStoreError
from cora.engine.memory_tool import MAX_FACT_CHARS, REMEMBER_TOOL_NAME, remember_tool
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.plugin import ToolCall, ToolRefusal
from fakes import FailingMemory, FakeMemory


def test_the_tool_stores_the_fact_the_model_passed() -> None:
    memory = FakeMemory()

    tool = remember_tool(memory)
    confirmation = tool.run(fact="trains on Tuesdays")

    assert [fact.text for fact in memory.recall()] == ["trains on Tuesdays"]
    assert "trains on Tuesdays" in confirmation


def test_a_store_that_cannot_be_written_refuses_rather_than_ending_the_turn() -> None:
    runtime = ToolRuntime(tools=(remember_tool(FailingMemory(MemoryStoreError())),))

    result = runtime.execute(
        ToolCall(name=REMEMBER_TOOL_NAME, arguments={"fact": "x"}, call_id="c1")
    )

    assert result.error is not None
    assert MemoryStoreError().user_message in result.error


def test_a_fact_longer_than_the_bound_is_refused() -> None:
    memory = FakeMemory()
    runtime = ToolRuntime(tools=(remember_tool(memory),))

    result = runtime.execute(
        ToolCall(
            name=REMEMBER_TOOL_NAME,
            arguments={"fact": "x" * (MAX_FACT_CHARS + 1)},
            call_id="c1",
        )
    )

    assert result.error is not None
    assert memory.recall() == ()


def test_a_fact_already_known_is_not_kept_twice() -> None:
    memory = FakeMemory(("trains on Tuesdays",))
    tool = remember_tool(memory)

    tool.run(fact="trains on Tuesdays")

    assert [fact.text for fact in memory.recall()] == ["trains on Tuesdays"]


def test_an_empty_fact_is_refused() -> None:
    memory = FakeMemory()
    tool = remember_tool(memory)

    with pytest.raises(ToolRefusal):
        tool.run(fact="   ")

    assert memory.recall() == ()
