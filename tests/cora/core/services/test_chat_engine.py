from collections.abc import Callable

import pytest

from cora.core.chunk import Chunk
from cora.core.citations import Context, Source
from cora.core.errors import InputRejectedError, LlmError, ToolLoopLimitError
from cora.core.ports.chat_model import ChatModel, ModelReply
from cora.core.ports.plugin import Tool, ToolCall, ToolResult
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.chat_engine import ChatEngine
from cora.core.services.steps import InputValidator, ToolExecutor
from cora.core.services.tool_runtime import ToolRuntime
from cora.core.services.validation import EmptyInputRule, ValidationPipeline
from cora.core.turn import Turn
from fakes import FailingChatModel, FakeContextSource, ScriptedChatModel, add_tool


def _make_engine(
    *,
    chat_model: ChatModel | None = None,
    knowledge_base: FakeContextSource | None = None,
    validation: InputValidator | None = None,
    tool_runtime: ToolExecutor | None = None,
    tools: tuple[Tool, ...] = (),
    top_k: int = 3,
    max_tool_rounds: int = 8,
    max_history_turns: int = 20,
    system_prompt: str = "You are a helpful assistant.",
    build_context: Callable[[list[RetrievedChunk]], Context] | None = None,
) -> ChatEngine:
    extra = {} if build_context is None else {"build_context": build_context}
    return ChatEngine(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        knowledge_base=knowledge_base or FakeContextSource(),
        validation=validation or ValidationPipeline((), ()),
        tool_runtime=tool_runtime or ToolRuntime(tools=()),
        tools=tools,
        top_k=top_k,
        max_tool_rounds=max_tool_rounds,
        max_history_turns=max_history_turns,
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


def test_answer_searches_the_knowledge_base_with_the_question_and_top_k() -> None:
    kb = FakeContextSource([_retrieved("a.txt")])
    engine = _make_engine(knowledge_base=kb, top_k=5)

    engine.answer("question")

    assert kb.last_query == "question"
    assert kb.last_k == 5


def test_answer_reports_only_the_cited_sources_under_their_own_numbers() -> None:
    kb = FakeContextSource([_retrieved("a.txt"), _retrieved("b.txt")])
    model = ScriptedChatModel([ModelReply(text="Per [2], do this.")])
    engine = _make_engine(chat_model=model, knowledge_base=kb, top_k=5)

    result = engine.answer("question")

    assert result.sources == (Source(2, "b.txt"),)


def test_answer_lists_cited_sources_in_ascending_number_order() -> None:
    kb = FakeContextSource([_retrieved("a.txt"), _retrieved("b.txt")])
    model = ScriptedChatModel([ModelReply(text="first [2], then [1].")])
    engine = _make_engine(chat_model=model, knowledge_base=kb, top_k=5)

    result = engine.answer("question")

    assert result.sources == (Source(1, "a.txt"), Source(2, "b.txt"))


def test_answer_reports_no_sources_when_the_answer_cites_none() -> None:
    kb = FakeContextSource([_retrieved("a.txt"), _retrieved("b.txt")])
    engine = _make_engine(knowledge_base=kb, top_k=5)

    result = engine.answer("question")

    assert result.sources == ()


def test_answer_resolves_citations_by_the_builders_own_numbers() -> None:
    context = Context(
        text="[5] x  [9] y",
        sources=(Source(5, "x.txt"), Source(9, "y.txt")),
    )
    model = ScriptedChatModel([ModelReply(text="see [9].")])
    engine = _make_engine(chat_model=model, build_context=lambda chunks: context)

    result = engine.answer("q")

    assert result.sources == (Source(9, "y.txt"),)


def test_answer_ignores_a_citation_whose_number_has_no_source() -> None:
    kb = FakeContextSource([_retrieved("a.txt")])
    model = ScriptedChatModel([ModelReply(text="Per [1] and also [9].")])
    engine = _make_engine(chat_model=model, knowledge_base=kb, top_k=5)

    result = engine.answer("question")

    assert result.sources == (Source(1, "a.txt"),)


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
        build_context=lambda chunks: Context(text="CUSTOM-CONTEXT", sources=()),
    )

    engine.answer("q")

    assert model.last_messages is not None
    system = model.last_messages[0]
    assert "CUSTOM-CONTEXT" in system.content
    assert "alpha" not in system.content


def test_answer_without_history_sends_only_system_and_current_question() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model)

    engine.answer("hi")

    assert model.last_messages is not None
    assert [m.role for m in model.last_messages] == ["system", "user"]
    assert model.last_messages[1].content == "hi"


def test_history_lands_between_system_prompt_and_current_question() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model)
    history = (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
    )

    engine.answer("What did I say my weight was?", history=history)

    assert model.last_messages is not None
    roles = [m.role for m in model.last_messages]
    assert roles == ["system", "user", "assistant", "user"]
    assert model.last_messages[1].content == "I weigh 80 kg."
    assert model.last_messages[2].content == "Noted."
    assert model.last_messages[3].content == "What did I say my weight was?"


def test_history_beyond_max_history_turns_drops_the_oldest_turns() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model, max_history_turns=2)
    history = (
        Turn(role="user", text="oldest"),
        Turn(role="assistant", text="old"),
        Turn(role="user", text="recent"),
        Turn(role="assistant", text="newest"),
    )

    engine.answer("q", history=history)

    assert model.last_messages is not None
    contents = [m.content for m in model.last_messages[1:-1]]
    assert contents == ["recent", "newest"]


def test_history_shorter_than_max_history_turns_is_sent_in_full() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model, max_history_turns=3)
    history = (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
    )

    engine.answer("q", history=history)

    assert model.last_messages is not None
    contents = [m.content for m in model.last_messages[1:-1]]
    assert contents == ["I weigh 80 kg.", "Noted."]


def test_history_exactly_at_max_history_turns_is_sent_in_full() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model, max_history_turns=2)
    history = (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
    )

    engine.answer("q", history=history)

    assert model.last_messages is not None
    contents = [m.content for m in model.last_messages[1:-1]]
    assert contents == ["I weigh 80 kg.", "Noted."]


def test_an_odd_cap_sends_a_leading_assistant_turn_without_its_question() -> None:
    """The plan accepts this orphan: the cap counts messages, not exchanges."""
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model, max_history_turns=3)
    history = (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
        Turn(role="user", text="And I'm 1.80 m."),
        Turn(role="assistant", text="Got it."),
    )

    engine.answer("q", history=history)

    assert model.last_messages is not None
    past = model.last_messages[1:-1]
    assert [m.content for m in past] == ["Noted.", "And I'm 1.80 m.", "Got it."]
    assert past[0].role == "assistant"


def test_zero_max_history_turns_sends_no_history_at_all() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    engine = _make_engine(chat_model=model, max_history_turns=0)
    history = (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
    )

    engine.answer("q", history=history)

    assert model.last_messages is not None
    assert [m.role for m in model.last_messages] == ["system", "user"]


class _RecordingValidator:
    def __init__(self) -> None:
        self.last_input: str | None = None

    def validate(self, user_input: str) -> str:
        self.last_input = user_input
        return user_input


def test_retrieval_and_validation_see_the_question_alone_not_the_history() -> None:
    kb = FakeContextSource()
    validator = _RecordingValidator()
    engine = _make_engine(knowledge_base=kb, validation=validator)
    history = (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
    )

    engine.answer("What about protein?", history=history)

    assert validator.last_input == "What about protein?"
    assert kb.last_query == "What about protein?"


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


def test_malformed_arguments_error_is_fed_back_as_data() -> None:
    call = ToolCall(name="add", arguments={"a": "one", "b": 2}, call_id="c1")
    model = ScriptedChatModel([ModelReply(tool_calls=(call,)), ModelReply(text="done")])
    engine = _make_engine(
        chat_model=model,
        tool_runtime=ToolRuntime(tools=(add_tool(),)),
        tools=(add_tool(),),
    )

    result = engine.answer("add one and 2")

    assert result.answer == "done"
    [tool_result] = result.tool_results
    assert tool_result.error is not None and "invalid arguments" in tool_result.error

    assert model.last_messages is not None
    fed_back = model.last_messages[-1]
    assert fed_back.role == "tool"
    assert fed_back.content == tool_result.error


def test_exceeding_max_tool_rounds_raises_tool_loop_limit_error() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    model = ScriptedChatModel([ModelReply(tool_calls=(call,))] * 2)
    engine = _make_engine(
        chat_model=model,
        tool_runtime=ToolRuntime(tools=(add_tool(),)),
        tools=(add_tool(),),
        max_tool_rounds=2,
    )

    with pytest.raises(ToolLoopLimitError):
        engine.answer("loop forever")


def test_invalid_input_is_rejected_before_kb_or_model_calls() -> None:
    kb = FakeContextSource([_retrieved("a.txt")])
    model = ScriptedChatModel([ModelReply(text="should not be used")])
    engine = _make_engine(
        chat_model=model,
        knowledge_base=kb,
        validation=ValidationPipeline((EmptyInputRule(),), ()),
    )

    with pytest.raises(InputRejectedError):
        engine.answer("   ")

    assert kb.last_query is None
    assert model.last_messages is None


def test_llm_error_from_the_chat_model_propagates_unchanged() -> None:
    error = LlmError()
    engine = _make_engine(chat_model=FailingChatModel(error))

    with pytest.raises(LlmError) as exc_info:
        engine.answer("hi")

    assert exc_info.value is error


def _describe(**kwargs: object) -> dict[str, int]:
    return {"value": 42}


_DICT_TOOL = Tool(
    name="describe",
    description="Return a dict.",
    parameter_schema={"type": "object", "properties": {}},
    run=_describe,
)


def test_non_string_tool_payload_is_fed_back_as_json() -> None:
    import json

    call = ToolCall(name="describe", arguments={}, call_id="c1")
    model = ScriptedChatModel([ModelReply(tool_calls=(call,)), ModelReply(text="ok")])
    engine = _make_engine(
        chat_model=model,
        tool_runtime=ToolRuntime(tools=(_DICT_TOOL,)),
        tools=(_DICT_TOOL,),
    )

    engine.answer("describe it")

    assert model.last_messages is not None
    fed_back = model.last_messages[-1]
    assert json.loads(fed_back.content) == {"value": 42}


def test_multiple_tool_calls_in_one_round_all_run_in_order() -> None:
    c1 = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    c2 = ToolCall(name="add", arguments={"a": 3, "b": 4}, call_id="c2")
    model = ScriptedChatModel(
        [ModelReply(tool_calls=(c1, c2)), ModelReply(text="done")]
    )
    engine = _make_engine(
        chat_model=model,
        tool_runtime=ToolRuntime(tools=(add_tool(),)),
        tools=(add_tool(),),
    )

    result = engine.answer("add two pairs")

    assert result.tool_results == (
        ToolResult(call_id="c1", payload=3),
        ToolResult(call_id="c2", payload=7),
    )
    assert model.last_messages is not None
    tool_ids = [m.tool_call_id for m in model.last_messages if m.role == "tool"]
    assert tool_ids == ["c1", "c2"]
