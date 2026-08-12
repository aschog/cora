"""The one test that runs the whole shipped stack against a real model: the real
composition root, the real Chroma store and embedder, OpenRouter over the network,
and the Streamlit page driven headlessly. It is the only cover for behaviour a stub
cannot show — a scripted model answers however the script says, so it can never
reveal the model ignoring an instruction. That is not hypothetical: the gate used to
ask the model to skip searching for small talk, and a real one searched anyway.
"""

import dataclasses
import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, build
from cora.app.config import Config

pytestmark = pytest.mark.llm

PROTEIN_DOC = b"""# Protein

For strength training, aim for 1.6 to 2.2 g of protein per kg of bodyweight per day.
Spread it over three or four meals.
"""
IN_THE_SUBJECT = "How much protein should I eat per kg of bodyweight?"
SMALL_TALK = "Hi there!"
SOURCES = "Sources"


def _live_config(store: Path) -> Config:
    """Both stores are redirected, documents and memory alike: an acceptance run that
    remembered things would write into whatever the developer is actually using."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is not set; the llm tier needs a real key")
    return dataclasses.replace(
        Config.from_env(),
        db_path=str(store / "chroma"),
        memory_path=str(store / "memory.sqlite"),
    )


def _live_app(store: Path) -> App:
    """The shipped composition root, pointed at stores of its own. Every default is
    the deployed one — the plugin, the model and the grounding text under test are
    whatever cora actually ships."""
    app = build(_live_config(store))
    app.knowledge_base.add_file(PROTEIN_DOC, "protein.md")
    return app


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.frontends.streamlit.chat import render

    render(app)


def _panels(at: AppTest) -> list[str]:
    """Scoped to the newest message: the same panel appears on every answered turn,
    so counting them across the page would say nothing about this one."""
    return [panel.label for panel in at.chat_message[-1].expander]


def test_a_real_model_answers_from_the_documents_but_greets_without_them(
    tmp_path: Path,
) -> None:
    """The question never says "my documents" — one that does gives the answer away,
    and the model answering a plain domain question from its own knowledge is the bug
    this guards. The greeting rides in the same run, because what must be told apart
    is two turns of one conversation, not two configurations."""
    at = AppTest.from_function(_page, args=(_live_app(tmp_path),)).run()

    at.chat_input[0].set_value(IN_THE_SUBJECT).run(timeout=180)

    assert not at.exception
    assert _panels(at) == [SOURCES], "the model answered without reaching the documents"
    [cited] = at.chat_message[-1].expander
    assert "protein.md" in "\n".join(line.value for line in cited.markdown)

    at.chat_input[0].set_value(SMALL_TALK).run(timeout=180)

    assert not at.exception
    assert _panels(at) == [], "small talk came back citing a document"


VEGETARIAN = "I'm vegetarian — keep that in mind."
WHAT_TO_EAT = "What should I eat after a session?"
MEAT = ("chicken", "beef", "steak", "salmon", "tuna", "pork", "turkey")


def test_a_real_model_keeps_what_it_is_told_and_uses_it_next_session(
    tmp_path: Path,
) -> None:
    """A scripted model calls `remember` because the script says so; only a real one
    can show that the rule in the brief is enough to make it call the tool, and that
    a fact recalled into a later brief actually changes the answer. The second
    session is a new page over the same memory file — a new thread with nothing in
    common but what was kept."""
    first = _live_app(tmp_path)
    at = AppTest.from_function(_page, args=(first,)).run()

    at.chat_input[0].set_value(VEGETARIAN).run(timeout=180)

    assert not at.exception
    assert first.memory is not None
    kept = " ".join(fact.text.lower() for fact in first.memory.recall())
    assert "vegetarian" in kept, "the model was told something durable and dropped it"

    later = AppTest.from_function(_page, args=(_live_app(tmp_path),)).run()
    later.chat_input[0].set_value(WHAT_TO_EAT).run(timeout=180)

    assert not later.exception
    answer = later.chat_message[-1].markdown[0].value.lower()
    assert not [meat for meat in MEAT if meat in answer], (
        "a remembered constraint was in the brief and the answer ignored it"
    )
