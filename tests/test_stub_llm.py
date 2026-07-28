import pytest

from cora.adapters.openrouter_chat_model import OpenRouterChatModel
from cora.core.ports.chat_model import Message, ModelReply
from fakes import add_tool
from stub_llm import StubLlm


def _model(stub: StubLlm) -> OpenRouterChatModel:
    return OpenRouterChatModel(
        model="stub-model", api_key="dummy-key", base_url=stub.base_url
    )


@pytest.mark.integration
def test_adapter_pointed_at_the_stub_returns_the_scripted_answer() -> None:
    """The stub stands in for OpenRouter at the network seam, so the real
    adapter — real langchain-openai, real HTTP — is the thing under test."""
    with StubLlm() as stub:
        stub.script_answer("Deadlifts train the posterior chain.")

        reply = _model(stub).complete((Message(role="user", content="Deadlifts?"),), ())

    assert reply == ModelReply(text="Deadlifts train the posterior chain.")


@pytest.mark.integration
def test_stub_asks_for_the_tool_until_the_result_comes_back() -> None:
    """Scripted on conversation state, not call count: the openai client retries,
    so an advancing script would desync. The predicate is whether the request
    already carries a tool result."""
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
