import dataclasses

import pytest

from cora.core.agent_state import AgentState
from cora.core.chunk import Chunk
from cora.core.citations import Source
from cora.core.errors import LlmError
from cora.core.ports.chat_model import Message, ModelReply
from cora.core.ports.plugin import ToolCall, ToolResult
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.retrieval_tool import SEARCH_TOOL_NAME, search_tool
from cora.core.services.steps import ModelStep, ToolStep
from cora.core.services.tool_runtime import ToolRuntime
from fakes import FailingChatModel, FakeContextSource, ScriptedChatModel, add_tool


def _hit(source: str, text: str = "protein builds muscle") -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=1.0
    )


def _asked(*calls: ToolCall, known: tuple[Source, ...] = ()) -> AgentState:
    reply = Message(role="assistant", content="", tool_calls=calls)
    return {"messages": [reply], "sources": list(known)}


def _search_call(call_id: str, name: str = SEARCH_TOOL_NAME) -> ToolCall:
    return ToolCall(name=name, arguments={"query": "protein"}, call_id=call_id)


def _searcher(*hits: RetrievedChunk, name: str = SEARCH_TOOL_NAME):
    tool = search_tool(FakeContextSource(list(hits)), top_k=3)
    return dataclasses.replace(tool, name=name)


def _add_call(call_id: str, a: int = 1, b: int = 2) -> ToolCall:
    return ToolCall(name="add", arguments={"a": a, "b": b}, call_id=call_id)


def test_a_tool_call_runs_and_its_result_lands_in_the_partial_state() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1")))

    assert partial["tool_results"] == [ToolResult(call_id="c1", payload=3)]
    [message] = partial["messages"]
    assert message.role == "tool"
    assert message.tool_call_id == "c1"


def test_a_payload_that_registers_nothing_is_fed_back_as_it_renders() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1")))

    [result] = partial["tool_results"]
    [message] = partial["messages"]
    assert message.content == result.render() == "3"
    assert partial["sources"] == []


def test_a_citable_payload_is_registered_and_its_result_renders_the_block() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("note.md")),)))

    partial = step(_asked(_search_call("c1")))

    [result] = partial["tool_results"]
    [message] = partial["messages"]
    assert "[1] note.md: protein builds muscle" in result.render()
    assert message.content == result.render()


def test_the_sources_it_registered_land_in_the_partial_state() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("note.md")),)))

    partial = step(_asked(_search_call("c1")))

    assert partial["sources"] == [Source(1, "note.md")]


def test_a_later_retrieval_in_the_same_run_continues_the_numbering() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("later.md")),)))

    partial = step(_asked(_search_call("c2"), known=(Source(1, "note.md"),)))

    assert partial["sources"] == [Source(2, "later.md")]
    [result] = partial["tool_results"]
    assert "[2] later.md" in result.render()


def test_any_tool_returning_a_citable_payload_is_registered_the_same_way() -> None:
    runtime = ToolRuntime(
        tools=(
            _searcher(_hit("note.md")),
            _searcher(_hit("diary.md"), name="recall"),
        )
    )

    partial = ToolStep(runtime)(
        _asked(_search_call("c1"), _search_call("c2", name="recall"))
    )

    assert partial["sources"] == [Source(1, "note.md"), Source(2, "diary.md")]
    searched, recalled = partial["tool_results"]
    assert "[1] note.md" in searched.render()
    assert "[2] diary.md" in recalled.render()


def test_several_calls_in_one_round_all_run_in_order() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1"), _add_call("c2", a=3, b=4)))

    assert partial["tool_results"] == [
        ToolResult(call_id="c1", payload=3),
        ToolResult(call_id="c2", payload=7),
    ]
    assert [m.tool_call_id for m in partial["messages"]] == ["c1", "c2"]


def test_an_unknown_tool_comes_back_as_a_tool_message() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(ToolCall(name="nope", arguments={}, call_id="c1")))

    [result] = partial["tool_results"]
    assert result.error is not None and "nope" in result.error
    [message] = partial["messages"]
    assert message.role == "tool"
    assert message.content == result.error


def test_malformed_arguments_come_back_as_a_tool_message() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(
        _asked(ToolCall(name="add", arguments={"a": "one", "b": 2}, call_id="c1"))
    )

    [result] = partial["tool_results"]
    assert result.error is not None and "invalid arguments" in result.error
    [message] = partial["messages"]
    assert message.content == result.error


def _model_step(*replies: ModelReply) -> ModelStep:
    return ModelStep(chat_model=ScriptedChatModel(list(replies)), tools=(add_tool(),))


def _asking(text: str = "add 1 and 2") -> AgentState:
    return {"messages": [Message(role="user", content=text)]}


def test_the_step_completes_with_the_states_messages_and_the_bound_tools() -> None:
    model = ScriptedChatModel([ModelReply(text="The sum is 3.")])
    step = ModelStep(chat_model=model, tools=(add_tool(),))
    state = _asking()

    partial = step(state)

    assert model.last_messages == tuple(state["messages"])
    assert model.last_tools == (add_tool(),)
    [reply] = partial["messages"]
    assert reply.role == "assistant"
    assert reply.content == "The sum is 3."


def test_a_tool_calling_reply_keeps_its_calls_ahead_of_the_rounds_tool_messages() -> (
    None
):
    state = _asking()
    from_model = _model_step(ModelReply(tool_calls=(_add_call("c1"),)))(state)
    asked: AgentState = {"messages": [*state["messages"], *from_model["messages"]]}

    from_tools = ToolStep(ToolRuntime(tools=(add_tool(),)))(asked)

    transcript = [*asked["messages"], *from_tools["messages"]]
    assert [m.role for m in transcript] == ["user", "assistant", "tool"]
    assert transcript[1].tool_calls == (_add_call("c1"),)


def test_a_final_reply_sets_the_answer_and_a_tool_calling_one_does_not() -> None:
    final = _model_step(ModelReply(text="The sum is 3."))(_asking())
    calling = _model_step(ModelReply(tool_calls=(_add_call("c1"),)))(_asking())

    assert final["answer"] == "The sum is 3."
    assert "answer" not in calling


def test_each_visit_adds_one_round() -> None:
    step = _model_step(ModelReply(text="one"), ModelReply(text="two"))

    assert step(_asking())["rounds"] == 1
    assert step(_asking())["rounds"] == 1


def test_an_llm_error_from_the_chat_model_propagates_unchanged() -> None:
    error = LlmError()
    step = ModelStep(chat_model=FailingChatModel(error), tools=())

    with pytest.raises(LlmError) as exc_info:
        step(_asking())

    assert exc_info.value is error
