from collections.abc import Iterator

import httpx
import openai
import pytest
from langchain_core.exceptions import ContextOverflowError
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
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
    LlmError,
    LlmKeyRejectedError,
    LlmMalformedToolCallError,
    LlmTimeoutError,
    LlmTruncatedError,
)
from cora.ports.chat_model import Message, ModelReply, Piece, Written
from cora.ports.plugin import ToolCall


def test_assistant_with_tool_calls_maps_to_ai_message() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")

    result = to_langchain_message(
        Message(role="assistant", content="", tool_calls=(call,))
    )

    assert isinstance(result, AIMessage)
    assert result.tool_calls == [
        {"name": "add", "args": {"a": 1, "b": 2}, "id": "c1", "type": "tool_call"}
    ]


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


def _streaming(*chunks: AIMessageChunk) -> type:
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
    written: list[Written] = []
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


def test_what_the_model_thinks_reaches_no_sink(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reasoning is not the answer, and a reader shown it would read it as one."""
    written: list[Written] = []
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

    assert written == [Piece("Sleep.")]


def test_a_stream_that_fails_part_way_keeps_the_category_and_what_was_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure travels as its category, and the pieces already sent are not taken
    back — the caller replaces them with the sentence the failure carries."""
    written: list[Written] = []

    class _BreaksMidStream:
        def __init__(self, **kwargs: object) -> None: ...

        def stream(self, messages: object) -> Iterator[AIMessageChunk]:
            yield AIMessageChunk(content="Sleep, ")
            raise openai.APITimeoutError(request=httpx.Request("POST", "https://x"))

    model = _model_over(monkeypatch, _BreaksMidStream)

    with pytest.raises(LlmTimeoutError):
        model.complete((Message(role="user", content="hi"),), (), written.append)

    assert written == [Piece("Sleep, ")]
