import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.core.ports.chat_model import ModelReply
from cora.core.ports.plugin import ToolCall
from cora.core.services.retrieval_tool import SEARCH_TOOL_NAME
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel, add_tool
from fixture_plugins import make_plugin

SEED_DOC = ("note.md", b"protein builds muscle")
QUESTION = "What do my notes say about protein, and what is 20 + 22?"
ANSWER = "Protein builds muscle [1], and 20 + 22 = 42."


def _call(name: str, call_id: str, **arguments: object) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=name, arguments=arguments, call_id=call_id),)
    )


def _app() -> App:
    return assemble(
        chat_model=ScriptedChatModel(
            [
                _call(SEARCH_TOOL_NAME, "call-1", query="protein"),
                _call("add", "call-2", a=20, b=22),
                ModelReply(text=ANSWER),
            ]
        ),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=make_plugin(tools=(add_tool(),), seed_docs=(SEED_DOC,)),
    )


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.app.ui.chat import render

    render(app)


@pytest.mark.integration
def test_the_trace_shows_each_step_with_its_tool_arguments_and_result() -> None:
    at = AppTest.from_function(_page, args=(_app(),)).run()

    at.chat_input[0].set_value(QUESTION).run()

    assert not at.exception
    assert ANSWER in "\n".join(md.value for md in at.markdown)

    [trace] = at.status
    assert trace.label == "How I got there"
    steps = "\n".join(md.value for md in trace.markdown)
    assert f"Decided to call {SEARCH_TOOL_NAME}" in steps
    assert f'{SEARCH_TOOL_NAME}(query="protein")' in steps
    assert "1 passage from note.md" in steps
    assert "add(a=20, b=22)" in steps
    assert "42" in steps
    assert "Decided no tool was needed" in steps
