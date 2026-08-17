import httpx
import openai
import pytest
from langchain_core.exceptions import ContextOverflowError
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from cora.adapters.openrouter_chat_model import (
    MAX_OUTPUT_TOKENS,
    MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
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

    def invoke(self, messages: object) -> AIMessage:
        return AIMessage(content="ok")


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
    model = OpenRouterChatModel(model="m", api_key="k", base_url="https://example/api")

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


def test_the_client_is_built_with_a_deadline_a_retry_count_and_a_cap() -> None:
    """The real client, not a fake taking kwargs: a name this library stopped reading
    would be swallowed into `model_kwargs` and the deadline would quietly not exist.
    Building one needs no network — nothing is sent until `invoke`.

    An agent makes several model calls per turn, so a request with no deadline is a turn
    that never ends, one attempt is a turn a single dropped connection ends, and no cap
    is an answer whose length the provider's default decides."""
    model = OpenRouterChatModel(model="m", api_key="k", base_url="https://example/api")

    client = model._client
    assert client.request_timeout == REQUEST_TIMEOUT_SECONDS
    assert client.max_retries == MAX_RETRIES
    assert client.max_tokens == MAX_OUTPUT_TOKENS


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

        def invoke(self, messages: object) -> AIMessage:
            raise raised

    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FailingChatOpenAI
    )
    model = OpenRouterChatModel(model="m", api_key="k", base_url="https://example/api")

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


def test_complete_returns_the_mapped_model_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FakeChatOpenAI
    )
    model = OpenRouterChatModel(model="m", api_key="k", base_url="https://example/api")

    reply = model.complete((Message(role="user", content="hi"),), ())

    assert reply == ModelReply(text="ok")
