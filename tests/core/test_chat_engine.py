from collections.abc import Callable

from core.chat_engine import ChatEngine, ToolExecutor, build_context_block
from core.chat_model import ChatModel, ModelReply
from core.chunk import Chunk
from core.plugin import Tool, ToolCall, ToolResult
from core.retrieval import RetrievedChunk
from core.tool_runtime import ToolRuntime
from fakes import FakeContextSource, ScriptedChatModel, add_tool


def _make_engine(
    *,
    chat_model: ChatModel | None = None,
    knowledge_base: FakeContextSource | None = None,
    tool_runtime: ToolExecutor | None = None,
    tools: tuple[Tool, ...] = (),
    top_k: int = 3,
    system_prompt: str = "You are a helpful assistant.",
    build_context: Callable[[list[RetrievedChunk]], str] | None = None,
) -> ChatEngine:
    extra = {} if build_context is None else {"build_context": build_context}
    return ChatEngine(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        knowledge_base=knowledge_base or FakeContextSource(),
        tool_runtime=tool_runtime or ToolRuntime(tools=()),
        tools=tools,
        top_k=top_k,
        system_prompt=system_prompt,
        **extra,
    )


def _retrieved(source: str, text: str = "t", score: float = 1.0) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=score
    )


def test_final_text_reply_becomes_the_answer() -> None:
    model = ScriptedChatModel([ModelReply(text="Hello!")])
    engine = _make_engine(chat_model=model)

    result = engine.answer("hi")

    assert result.answer == "Hello!"
    assert result.tool_results == ()


def test_answer_searches_the_knowledge_base_and_reports_unique_sources() -> None:
    kb = FakeContextSource(
        [_retrieved("a.txt"), _retrieved("a.txt"), _retrieved("b.txt")]
    )
    engine = _make_engine(knowledge_base=kb, top_k=5)

    result = engine.answer("question")

    assert kb.last_query == "question"
    assert kb.last_k == 5
    assert result.sources == ("a.txt", "b.txt")


def test_build_context_block_numbers_chunks_and_states_citation_rule() -> None:
    block = build_context_block(
        [_retrieved("a.txt", text="alpha"), _retrieved("b.txt", text="beta")]
    )

    assert block.index("[1]") < block.index("[2]")
    assert "alpha" in block and "a.txt" in block
    assert "beta" in block and "b.txt" in block
    assert "cite" in block.lower()


def test_system_message_embeds_the_prompt_and_context_block() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    kb = FakeContextSource([_retrieved("a.txt", text="alpha")])
    engine = _make_engine(chat_model=model, knowledge_base=kb, system_prompt="SYS")

    engine.answer("q")

    assert model.last_messages is not None
    system = model.last_messages[0]
    assert system.role == "system"
    assert "SYS" in system.content
    assert "alpha" in system.content and "[1]" in system.content


def test_injected_build_context_replaces_the_default() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    kb = FakeContextSource([_retrieved("a.txt", text="alpha")])
    engine = _make_engine(
        chat_model=model,
        knowledge_base=kb,
        build_context=lambda chunks: "CUSTOM-CONTEXT",
    )

    engine.answer("q")

    assert model.last_messages is not None
    system = model.last_messages[0]
    assert "CUSTOM-CONTEXT" in system.content
    assert "alpha" not in system.content


def test_tool_call_runs_and_result_feeds_back_and_appears_in_result() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    model = ScriptedChatModel(
        [ModelReply(tool_calls=(call,)), ModelReply(text="The sum is 3.")]
    )
    engine = _make_engine(
        chat_model=model,
        tool_runtime=ToolRuntime(tools=(add_tool(),)),
        tools=(add_tool(),),
    )

    result = engine.answer("add 1 and 2")

    assert result.answer == "The sum is 3."
    assert result.tool_results == (ToolResult(call_id="c1", payload=3),)

    assert model.last_messages is not None
    tool_message = model.last_messages[-1]
    assert tool_message.role == "tool"
    assert tool_message.tool_call_id == "c1"
    assert "3" in tool_message.content


def test_unknown_tool_error_is_fed_back_as_data_and_loop_finishes() -> None:
    call = ToolCall(name="nope", arguments={}, call_id="c1")
    model = ScriptedChatModel([ModelReply(tool_calls=(call,)), ModelReply(text="done")])
    engine = _make_engine(
        chat_model=model,
        tool_runtime=ToolRuntime(tools=(add_tool(),)),
        tools=(add_tool(),),
    )

    result = engine.answer("use a missing tool")

    assert result.answer == "done"
    [tool_result] = result.tool_results
    assert tool_result.error is not None and "nope" in tool_result.error

    assert model.last_messages is not None
    fed_back = model.last_messages[-1]
    assert fed_back.role == "tool"
    assert fed_back.content == tool_result.error
