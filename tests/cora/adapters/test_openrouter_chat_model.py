import logging
from collections.abc import Iterator

import httpx
import openai
import pytest
from langchain_core.exceptions import ContextOverflowError
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from cora.adapters.openrouter_chat_model import (
    MAX_RETRIES,
    OpenRouterChatModel,
    to_langchain_message,
    to_model_reply,
)
from cora.domain.errors import (
    LlmBusyError,
    LlmConversationTooLongError,
    LlmEmptyReplyError,
    LlmError,
    LlmKeyRejectedError,
    LlmMalformedToolCallError,
    LlmTimeoutError,
    LlmTruncatedError,
)
from cora.ports.chat_model import Message, ModelReply
from cora.ports.plugin import ToolCall
from fakes import add_tool


class _FakeChatOpenAI:
    last: "_FakeChatOpenAI | None" = None

    def __init__(self, **kwargs: object) -> None:
        _FakeChatOpenAI.last = self
        self.init_kwargs = kwargs
        self.bound_tools: list[dict[str, object]] | None = None

    def bind_tools(self, tools: list[dict[str, object]]) -> "_FakeChatOpenAI":
        self.bound_tools = tools
        return self

    def stream(self, messages: object) -> Iterator[AIMessageChunk]:
        yield AIMessageChunk(content="ok")


def test_system_message_maps_to_langchain_system_message() -> None:
    result = to_langchain_message(Message(role="system", content="sys"))

    assert isinstance(result, SystemMessage)
    assert result.content == "sys"


def test_user_message_maps_to_human_message() -> None:
    result = to_langchain_message(Message(role="user", content="hi"))

    assert isinstance(result, HumanMessage)
    assert result.content == "hi"


def test_assistant_with_tool_calls_maps_to_ai_message() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")

    result = to_langchain_message(
        Message(role="assistant", content="", tool_calls=(call,))
    )

    assert isinstance(result, AIMessage)
    assert result.tool_calls == [
        {"name": "add", "args": {"a": 1, "b": 2}, "id": "c1", "type": "tool_call"}
    ]


def test_tool_message_maps_to_langchain_tool_message() -> None:
    result = to_langchain_message(Message(role="tool", content="3", tool_call_id="c1"))

    assert isinstance(result, ToolMessage)
    assert result.content == "3"
    assert result.tool_call_id == "c1"


def test_provider_reply_with_tool_calls_becomes_model_reply_tool_calls() -> None:
    ai = AIMessage(
        content="",
        tool_calls=[
            {"name": "add", "args": {"a": 1, "b": 2}, "id": "c1", "type": "tool_call"}
        ],
    )

    reply = to_model_reply(ai)

    assert reply == ModelReply(
        text="",
        tool_calls=(ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1"),),
    )
    assert reply.is_final is False


def test_provider_text_reply_becomes_final_model_reply() -> None:
    reply = to_model_reply(AIMessage(content="The sum is 3."))

    assert reply == ModelReply(text="The sum is 3.", tool_calls=())
    assert reply.is_final is True


def test_tool_schemas_are_bound_onto_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FakeChatOpenAI
    )
    tool = add_tool()
    model = OpenRouterChatModel(
        model="m",
        api_key="k",
        base_url="https://example/api",
        max_output_tokens=1024,
        request_timeout_seconds=30,
        reasoning_effort="low",
    )

    model.complete((Message(role="user", content="hi"),), (tool,))

    assert _FakeChatOpenAI.last is not None
    assert _FakeChatOpenAI.last.bound_tools == [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameter_schema,
            },
        }
    ]


def test_the_client_is_built_with_the_budgets_it_was_handed() -> None:
    """The real client, not a fake taking kwargs: a name this library stopped reading
    would be swallowed into `model_kwargs` and the deadline would quietly not exist.
    Building one needs no network — nothing is sent until the stream opens.

    The numbers come from the caller because they belong to the model the deployment
    named: what a reasoning model needs to think and answer within is not what the
    adapter can know."""
    model = OpenRouterChatModel(
        model="m",
        api_key="k",
        base_url="https://example/api",
        max_output_tokens=1234,
        request_timeout_seconds=77,
        reasoning_effort="low",
    )

    client = model._client
    assert client.max_tokens == 1234
    assert client.request_timeout == 77
    assert client.max_retries == MAX_RETRIES


def test_the_client_asks_for_the_reasoning_effort_it_was_handed() -> None:
    """A reasoning model bills its thinking to the same budget it answers from, so how
    hard it thinks decides what is left to answer with — and the provider's own default
    is not the one measured to answer fastest here."""
    model = OpenRouterChatModel(
        model="m",
        api_key="k",
        base_url="https://example/api",
        max_output_tokens=1234,
        request_timeout_seconds=77,
        reasoning_effort="high",
    )

    assert model._client.extra_body == {"reasoning": {"effort": "high"}}


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (
            openai.APITimeoutError(request=httpx.Request("POST", "https://example")),
            LlmTimeoutError,
        ),
        (
            openai.RateLimitError(
                "slow down",
                response=httpx.Response(
                    429, request=httpx.Request("POST", "https://example")
                ),
                body=None,
            ),
            LlmBusyError,
        ),
        (
            openai.AuthenticationError(
                "bad key",
                response=httpx.Response(
                    401, request=httpx.Request("POST", "https://example")
                ),
                body=None,
            ),
            LlmKeyRejectedError,
        ),
        (ContextOverflowError("too long"), LlmConversationTooLongError),
        (RuntimeError("provider down"), LlmError),
    ],
)
def test_a_provider_failure_keeps_the_category_the_user_can_act_on(
    monkeypatch: pytest.MonkeyPatch, raised: Exception, expected: type[LlmError]
) -> None:
    """Waiting out a rate limit and retrying a timeout are different advice, and one
    generic message can only give one of them. Two of these no retry ever fixes: a
    rejected key, and a conversation the model can no longer read — the thread is
    persisted, so "please try again" overflows identically until a new one starts."""

    class _FailingChatOpenAI:
        def __init__(self, **kwargs: object) -> None: ...

        def stream(self, messages: object) -> Iterator[AIMessageChunk]:
            raise raised
            yield

    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FailingChatOpenAI
    )
    model = OpenRouterChatModel(
        model="m",
        api_key="k",
        base_url="https://example/api",
        max_output_tokens=1024,
        request_timeout_seconds=30,
        reasoning_effort="low",
    )

    with pytest.raises(expected):
        model.complete((Message(role="user", content="hi"),), ())


def test_an_answer_cut_off_at_the_token_limit_is_not_an_answer() -> None:
    truncated = AIMessage(
        content="Your daily protein target is",
        response_metadata={"finish_reason": "length"},
    )

    with pytest.raises(LlmTruncatedError):
        to_model_reply(truncated)


def test_a_final_reply_with_nothing_in_it_is_not_an_answer() -> None:
    """No text and no tool call is a turn the user would see as a blank bubble."""
    with pytest.raises(LlmEmptyReplyError):
        to_model_reply(AIMessage(content=""))


def test_a_tool_round_may_carry_no_text_at_all() -> None:
    """The empty-reply check is about *finals*: asking for a tool is how a round starts,
    and it says nothing to the user by design."""
    reply = to_model_reply(
        AIMessage(
            content="",
            tool_calls=[
                {"name": "add", "args": {"a": 1}, "id": "c1", "type": "tool_call"}
            ],
            response_metadata={"finish_reason": "tool_calls"},
        )
    )

    assert reply.is_final is False


def test_a_tool_call_the_model_malformed_is_not_an_answer() -> None:
    """The call the model wrote is gone before cora sees it — `tool_calls` is empty and
    the prose beside it reads as a final. It is a turn that failed, and the search it
    asked for is what the answer would have rested on."""
    malformed = AIMessage(
        content="Let me check your notes.",
        invalid_tool_calls=[
            {
                "name": "search_documents",
                "args": '{"query": ',
                "id": "c1",
                "error": "Unterminated string",
                "type": "invalid_tool_call",
            }
        ],
    )

    with pytest.raises(LlmMalformedToolCallError):
        to_model_reply(malformed)


def test_one_call_that_parsed_beside_one_that_did_not_is_still_a_failed_turn() -> None:
    """A round that runs the calls it can and drops the rest answers on half of what the
    model asked for, with nothing saying which half."""
    half = AIMessage(
        content="",
        tool_calls=[
            {"name": "add", "args": {"a": 1}, "id": "c1", "type": "tool_call"},
        ],
        invalid_tool_calls=[
            {
                "name": "search_documents",
                "args": "not json",
                "id": "c2",
                "error": None,
                "type": "invalid_tool_call",
            }
        ],
    )

    with pytest.raises(LlmMalformedToolCallError):
        to_model_reply(half)


def test_the_parse_failure_is_logged_and_the_reader_is_told_none_of_it(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """What the model wrote is the only way to find out why it broke, and it is no part
    of a sentence the reader can act on."""
    malformed = AIMessage(
        content="",
        invalid_tool_calls=[
            {
                "name": "search_documents",
                "args": '{"query": ',
                "id": "c1",
                "error": "Unterminated string",
                "type": "invalid_tool_call",
            }
        ],
    )

    with (
        caplog.at_level(logging.WARNING, logger="cora.adapters"),
        pytest.raises(LlmMalformedToolCallError) as raised,
    ):
        to_model_reply(malformed)

    logged = caplog.text
    assert "search_documents" in logged
    assert "Unterminated string" in logged
    assert "search_documents" not in raised.value.user_message


def test_complete_returns_the_mapped_model_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FakeChatOpenAI
    )
    model = OpenRouterChatModel(
        model="m",
        api_key="k",
        base_url="https://example/api",
        max_output_tokens=1024,
        request_timeout_seconds=30,
        reasoning_effort="low",
    )

    reply = model.complete((Message(role="user", content="hi"),), ())

    assert reply == ModelReply(text="ok")


def _streaming(*chunks: AIMessageChunk) -> type:
    """A client that streams the chunks it was built over. It offers no `invoke`, so an
    adapter that asked for the whole reply at once would fail rather than quietly stop
    streaming."""

    class _Streaming:
        def __init__(self, **kwargs: object) -> None: ...

        def bind_tools(self, tools: list[dict[str, object]]) -> "_Streaming":
            return self

        def stream(self, messages: object) -> Iterator[AIMessageChunk]:
            yield from chunks

    return _Streaming


def _model_over(monkeypatch: pytest.MonkeyPatch, client: type) -> OpenRouterChatModel:
    monkeypatch.setattr("cora.adapters.openrouter_chat_model.ChatOpenAI", client)
    return OpenRouterChatModel(
        model="m",
        api_key="k",
        base_url="https://example/api",
        max_output_tokens=1024,
        request_timeout_seconds=30,
        reasoning_effort="low",
    )


def test_each_piece_the_model_writes_reaches_the_sink(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    written: list[str] = []
    model = _model_over(
        monkeypatch,
        _streaming(
            AIMessageChunk(content="Sleep, "), AIMessageChunk(content="not volume.")
        ),
    )

    model.complete((Message(role="user", content="hi"),), (), written.append)

    assert written == ["Sleep, ", "not volume."]


def test_a_streamed_reply_is_the_reply_a_whole_response_would_have_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Streaming is how the text arrives, not what the turn is made of: the state, the
    transcript and the recorded turn all come off this reply."""
    model = _model_over(
        monkeypatch,
        _streaming(
            AIMessageChunk(content="Sleep, "),
            AIMessageChunk(
                content="not volume.", response_metadata={"finish_reason": "stop"}
            ),
        ),
    )

    reply = model.complete((Message(role="user", content="hi"),), ())

    assert reply == ModelReply(text="Sleep, not volume.")


def test_a_streamed_tool_call_arrives_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    """A provider sends the arguments in fragments of JSON, which is unparseable until
    the last of them has arrived."""
    written: list[str] = []
    model = _model_over(
        monkeypatch,
        _streaming(
            AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {
                        "name": "search_documents",
                        "args": '{"query":',
                        "id": "c1",
                        "index": 0,
                        "type": "tool_call_chunk",
                    }
                ],
            ),
            AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {
                        "name": None,
                        "args": '"bm25"}',
                        "id": None,
                        "index": 0,
                        "type": "tool_call_chunk",
                    }
                ],
            ),
        ),
    )

    reply = model.complete((Message(role="user", content="hi"),), (), written.append)

    assert reply.tool_calls == (
        ToolCall(name="search_documents", arguments={"query": "bm25"}, call_id="c1"),
    )
    assert written == []


def test_a_streamed_tool_call_whose_arguments_never_parse_ends_the_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fragments are unparseable until the last has arrived, so a call that is still
    broken once the stream is whole is broken for good."""
    written: list[str] = []
    model = _model_over(
        monkeypatch,
        _streaming(
            AIMessageChunk(content="Let me check your notes. "),
            AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {
                        "name": "search_documents",
                        "args": "bm25",
                        "id": "c1",
                        "index": 0,
                        "type": "tool_call_chunk",
                    }
                ],
            ),
        ),
    )

    with pytest.raises(LlmMalformedToolCallError):
        model.complete((Message(role="user", content="hi"),), (), written.append)


def test_what_the_model_thinks_reaches_no_sink(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reasoning is not the answer, and a reader shown it would read it as one."""
    written: list[str] = []
    model = _model_over(
        monkeypatch,
        _streaming(
            AIMessageChunk(
                content="", additional_kwargs={"reasoning_content": "weighing sleep"}
            ),
            AIMessageChunk(content="Sleep."),
        ),
    )

    model.complete((Message(role="user", content="hi"),), (), written.append)

    assert written == ["Sleep."]


def test_a_stream_cut_off_at_the_token_limit_is_still_not_an_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pieces already written are half a sentence; what the check reads is the
    reason the provider gave for stopping, which only the last chunk carries."""
    model = _model_over(
        monkeypatch,
        _streaming(
            AIMessageChunk(content="Your daily protein target is"),
            AIMessageChunk(content="", response_metadata={"finish_reason": "length"}),
        ),
    )

    with pytest.raises(LlmTruncatedError):
        model.complete((Message(role="user", content="hi"),), ())


def test_a_stream_that_aggregates_to_nothing_is_still_not_an_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model_over(monkeypatch, _streaming(AIMessageChunk(content="")))

    with pytest.raises(LlmEmptyReplyError):
        model.complete((Message(role="user", content="hi"),), ())


def test_a_stream_that_arrives_empty_is_not_an_answer_either(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No chunks at all: there is no reply to map, and a turn cannot be built from
    one that was never sent."""
    model = _model_over(monkeypatch, _streaming())

    with pytest.raises(LlmEmptyReplyError):
        model.complete((Message(role="user", content="hi"),), ())


def test_a_stream_that_fails_part_way_keeps_the_category_and_what_was_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure travels as its category, and the pieces already sent are not taken
    back — the caller replaces them with the sentence the failure carries."""
    written: list[str] = []

    class _BreaksMidStream:
        def __init__(self, **kwargs: object) -> None: ...

        def stream(self, messages: object) -> Iterator[AIMessageChunk]:
            yield AIMessageChunk(content="Sleep, ")
            raise openai.APITimeoutError(request=httpx.Request("POST", "https://x"))

    model = _model_over(monkeypatch, _BreaksMidStream)

    with pytest.raises(LlmTimeoutError):
        model.complete((Message(role="user", content="hi"),), (), written.append)

    assert written == ["Sleep, "]
