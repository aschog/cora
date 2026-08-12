from cora.engine.memory_tool import REMEMBER_TOOL_NAME, remember_tool
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.plugin import ToolCall
from fakes import FakeMemory


def test_the_tool_stores_the_fact_the_model_passed() -> None:
    memory = FakeMemory()

    tool = remember_tool(memory)
    confirmation = tool.run(fact="trains on Tuesdays")

    assert [fact.text for fact in memory.recall()] == ["trains on Tuesdays"]
    assert "trains on Tuesdays" in confirmation


def test_a_call_with_no_fact_comes_back_an_invalid_arguments_error() -> None:
    runtime = ToolRuntime(tools=(remember_tool(FakeMemory()),))

    result = runtime.execute(
        ToolCall(name=REMEMBER_TOOL_NAME, arguments={}, call_id="c1")
    )

    assert result.error is not None
    assert "invalid arguments" in result.error


def test_a_remembered_fact_is_confirmed_through_the_runtime() -> None:
    memory = FakeMemory()
    runtime = ToolRuntime(tools=(remember_tool(memory),))

    result = runtime.execute(
        ToolCall(
            name=REMEMBER_TOOL_NAME,
            arguments={"fact": "is vegetarian"},
            call_id="c1",
        )
    )

    assert result.error is None
    assert [fact.text for fact in memory.recall()] == ["is vegetarian"]
