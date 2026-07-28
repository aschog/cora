import pytest

from cora.adapters.openrouter_chat_model import OpenRouterChatModel
from cora.core.errors import LlmError
from cora.core.ports.chat_model import Message, ModelReply
from fakes import add_tool
from stub_llm import StubLlm


def _model(stub: StubLlm) -> OpenRouterChatModel:
    return OpenRouterChatModel(
        model="stub-model", api_key="dummy-key", base_url=stub.base_url
    )


@pytest.mark.integration
def test_adapter_pointed_at_the_stub_returns_the_scripted_answer() -> None:
    with StubLlm() as stub:
        stub.script_answer("Deadlifts train the posterior chain.")

        reply = _model(stub).complete((Message(role="user", content="Deadlifts?"),), ())

    assert reply == ModelReply(text="Deadlifts train the posterior chain.")


@pytest.mark.integration
def test_stub_asks_for_the_tool_until_the_result_comes_back() -> None:
    tool = add_tool()
    question = (Message(role="user", content="Add 1 and 2."),)
    with StubLlm() as stub:
        stub.script_tool_call("add", {"a": 1, "b": 2})
        stub.script_answer("The sum is 3.")
        model = _model(stub)

        asked = model.complete(question, (tool,))
        answered = model.complete(
            (
                *question,
                Message(role="assistant", content="", tool_calls=asked.tool_calls),
                Message(
                    role="tool", content="3", tool_call_id=asked.tool_calls[0].call_id
                ),
            ),
            (tool,),
        )

    assert [(c.name, c.arguments) for c in asked.tool_calls] == [
        ("add", {"a": 1, "b": 2})
    ]
    assert asked.tool_calls[0].call_id
    assert asked.is_final is False
    assert answered == ModelReply(text="The sum is 3.")


@pytest.mark.integration
def test_repeating_a_request_does_not_advance_the_script() -> None:
    tool = add_tool()
    question = (Message(role="user", content="Add 1 and 2."),)
    with StubLlm() as stub:
        stub.script_tool_call("add", {"a": 1, "b": 2})
        stub.script_answer("The sum is 3.")
        model = _model(stub)

        first = model.complete(question, (tool,))
        repeated = model.complete(question, (tool,))

    assert first == repeated
    assert repeated.is_final is False


@pytest.mark.integration
def test_stub_records_what_the_model_was_sent() -> None:
    tool = add_tool()
    opening = (
        Message(role="system", content="You are terse."),
        Message(role="user", content="Add 1 and 2."),
    )
    with StubLlm() as stub:
        stub.script_tool_call("add", {"a": 1, "b": 2})
        stub.script_answer("The sum is 3.")
        model = _model(stub)

        asked = model.complete(opening, (tool,))
        call_id = asked.tool_calls[0].call_id
        model.complete(
            (
                *opening,
                Message(role="assistant", content="", tool_calls=asked.tool_calls),
                Message(role="tool", content="3", tool_call_id=call_id),
            ),
            (tool,),
        )

    assert [[m["role"] for m in r["messages"]] for r in stub.requests] == [
        ["system", "user"],
        ["system", "user", "assistant", "tool"],
    ]
    assert stub.requests[0]["messages"][0]["content"] == "You are terse."
    assert stub.requests[-1]["messages"][-1]["tool_call_id"] == call_id


@pytest.mark.integration
def test_stub_records_every_retry_of_a_failed_request() -> None:
    with StubLlm() as stub:
        stub.script_status(429)

        with pytest.raises(LlmError):
            _model(stub).complete((Message(role="user", content="Deadlifts?"),), ())

    assert len(stub.requests) == 3


@pytest.mark.integration
def test_scripted_rate_limit_surfaces_as_the_apps_llm_error() -> None:
    """One status is enough: every provider failure collapses to LlmError, and the
    per-status mapping is already covered by the adapter's unit tests."""
    with StubLlm() as stub:
        stub.script_status(429)

        with pytest.raises(LlmError):
            _model(stub).complete((Message(role="user", content="Deadlifts?"),), ())
