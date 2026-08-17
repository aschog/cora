import httpx
import openai
import pytest
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from cora.adapters.openrouter_chat_model import (
    MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
    OpenRouterChatModel,
    to_langchain_message,
    to_model_reply,
)
from cora.domain.errors import (
    LlmBusyError,
    LlmEmptyReplyError,
    LlmError,
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


def test_provider_exception_is_wrapped_as_llm_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FailingChatOpenAI:
        def __init__(self, **kwargs: object) -> None: ...

        def invoke(self, messages: object) -> AIMessage:
            raise RuntimeError("provider down")

    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FailingChatOpenAI
    )
    model = OpenRouterChatModel(model="m", api_key="k", base_url="https://example/api")

    with pytest.raises(LlmError):
        model.complete((Message(role="user", content="hi"),), ())


def test_the_client_is_given_a_deadline_and_a_retry_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An agent makes several model calls per turn, so a request with no deadline is a
    turn that never ends, and one attempt is a turn a single dropped connection ends."""
    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FakeChatOpenAI
    )

    OpenRouterChatModel(model="m", api_key="k", base_url="https://example/api")

    assert _FakeChatOpenAI.last is not None
    assert _FakeChatOpenAI.last.init_kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS
    assert _FakeChatOpenAI.last.init_kwargs["max_retries"] == MAX_RETRIES


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
        (RuntimeError("provider down"), LlmError),
    ],
)
def test_a_provider_failure_keeps_the_category_the_user_can_act_on(
    monkeypatch: pytest.MonkeyPatch, raised: Exception, expected: type[LlmError]
) -> None:
    """Waiting out a rate limit and retrying a timeout are different advice, and one
    generic message can only give one of them."""

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
