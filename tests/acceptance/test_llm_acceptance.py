"""The tests that run the whole shipped stack against a real model: the real
composition root, the real Chroma store and embedder, OpenRouter over the network,
and the Streamlit page driven headlessly. They are the only cover for behaviour a stub
cannot show — a scripted model answers however the script says, so it can never
reveal the model ignoring an instruction. Since story 15 removed the grounding gate,
these are the only tests that can catch a model answering a document question from
what it happens to know.
"""

import dataclasses
import os
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from apptest import ANSWER_COMPONENT, PANE_COMPONENT, answers, mounted_html
from cora.app.assembly import App, build
from cora.app.config import Config
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.streamlit.viewer import OPEN_CITATION
from cora.plugins.fitness.tools import DAILY_ENERGY_TOOL

pytestmark = pytest.mark.llm

PROTEIN_DOC = b"""# Protein

For strength training, aim for 1.6 to 2.2 g of protein per kg of bodyweight per day.
Spread it over three or four meals.
"""
IN_THE_SUBJECT = "How much protein should I eat per kg of bodyweight?"
LIVE_PLUGINS = ("cora.plugins.security", "cora.plugins.fitness")
SMALL_TALK = "Hi there!"
SOURCES = "Sources"


def _live_config(store: Path) -> Config:
    """Both stores are redirected, documents and memory alike: an acceptance run that
    remembered things would write into whatever the developer is actually using. The
    domain is named here rather than taken from the default set, which ships the guard
    alone — a training question needs a plugin that claims training as its subject."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is not set; the llm tier needs a real key")
    return dataclasses.replace(
        Config.from_env(),
        plugin_modules=LIVE_PLUGINS,
        db_path=str(store / "chroma"),
        memory_path=str(store / "memory.sqlite"),
        documents_path=str(store / "documents.sqlite"),
    )


def _live_app(store: Path) -> App:
    """The shipped composition root, pointed at stores of its own. Every other default
    is the deployed one — the model, the preamble and the reminder under test are
    whatever cora actually ships."""
    return build(_live_config(store))


def _holding_the_protein_doc(store: Path) -> App:
    """Indexed behind the page's back, for the tests whose subject starts at the
    question. The happy path uploads the same document through the widget instead."""
    app = _live_app(store)
    app.knowledge_base.add_file(PROTEIN_DOC, "protein.md")
    return app


def _page(app) -> None:  # AppTest re-executes this without the module's globals
    from cora.frontends.streamlit.chat import render

    render(app)


def _panels(at: AppTest) -> list[str]:
    """Scoped to the newest message: the same panel appears on every answered turn,
    so counting them across the page would say nothing about this one."""
    return [panel.label for panel in at.chat_message[-1].expander]


def _steps(at: AppTest) -> str:
    """The newest turn's trace. One status holds one turn's steps, and every earlier
    turn is redrawn on every rerun, so the last one is this turn's."""
    return "\n".join(line.value for line in at.status[-1].code)


def _sidebar(at: AppTest) -> str:
    return "\n".join(md.value for md in at.sidebar.markdown)


UPLOADED = ("protein.md", PROTEIN_DOC, "text/markdown")
ONE_CHUNK = "1 chunk"
CITATION = re.compile(r"\[\d+]")
NEEDS_THE_CALCULATOR = (
    "I'm a 34-year-old man, 80 kg at 180 cm, training hard four times a week. "
    "What is my total daily energy expenditure?"
)
KEEP_THIS = "Remember that I'm vegetarian."
FAILED = "⚠️"


def test_a_whole_session_uploads_asks_calculates_and_remembers(tmp_path: Path) -> None:
    """The demo as one conversation on one thread: the document goes in through the
    uploader, the answer comes back cited from it, the calculation goes to the
    plugin's tool instead of the model's arithmetic, and a fact the user asks it to
    keep reaches the store the sidebar reads. Every assertion is on a widget or on the
    trace, so what the test walks is the sequence the code takes."""
    app = _live_app(tmp_path)
    at = AppTest.from_function(_page, args=(app,)).run()

    at.file_uploader[0].set_value(UPLOADED)
    at.run(timeout=180)  # the embedder loads on this first use

    assert not at.exception
    [added] = at.success
    assert "protein.md" in added.value
    assert ONE_CHUNK in added.value
    assert "protein.md" in _sidebar(at)

    at.chat_input[0].set_value(IN_THE_SUBJECT).run(timeout=180)

    assert not at.exception
    assert _panels(at) == [SOURCES], "the model answered without reaching the documents"
    [cited] = at.chat_message[-1].expander
    assert "protein.md" in "\n".join(line.value for line in cited.markdown)
    [answered] = answers(at)
    assert CITATION.search(answered), (
        f"the answer rested on a passage it never cited: {answered!r}"
    )
    assert f"{SEARCH_TOOL_NAME}(" in _steps(at)

    at.chat_input[0].set_value(NEEDS_THE_CALCULATOR).run(timeout=180)

    assert not at.exception
    calculated = _steps(at)
    assert f"{DAILY_ENERGY_TOOL.name}(" in calculated, (
        "the model did the arithmetic itself instead of calling the plugin's tool"
    )
    assert FAILED not in calculated

    at.chat_input[0].set_value(KEEP_THIS).run(timeout=180)

    assert not at.exception
    assert f"{REMEMBER_TOOL_NAME}(" in _steps(at)
    assert app.memory is not None
    kept = " ".join(fact.text.lower() for fact in app.memory.recall())
    assert "vegetarian" in kept
    assert "vegetarian" in _sidebar(at).lower()


def test_a_real_model_answers_from_the_documents_but_greets_without_them(
    tmp_path: Path,
) -> None:
    """The question never says "my documents" — one that does gives the answer away,
    and the model answering a plain domain question from its own knowledge is the bug
    this guards. The greeting rides in the same run, because what must be told apart
    is two turns of one conversation, not two configurations."""
    at = AppTest.from_function(_page, args=(_holding_the_protein_doc(tmp_path),)).run()

    at.chat_input[0].set_value(IN_THE_SUBJECT).run(timeout=180)

    assert not at.exception
    assert _panels(at) == [SOURCES], "the model answered without reaching the documents"
    [cited] = at.chat_message[-1].expander
    assert "protein.md" in "\n".join(line.value for line in cited.markdown)

    at.chat_input[0].set_value(SMALL_TALK).run(timeout=180)

    assert not at.exception
    assert _panels(at) == [], "small talk came back citing a document"


ASKS_FOR_DOCUMENTS = ("upload", "no documents", "don't have any documents", "share")
GREETS = ("hi", "hello", "hey", "nice to meet")
"""The greeting is checked for *being a greeting*, which is all story 12 claims for it.
An empty store is a fact about the app, and a real model volunteers it while greeting —
"nice to meet you; I don't have any documents from you yet, how can I help?" is small
talk answered as small talk, so an assertion that no upload is ever mentioned would be
testing a rule nobody wrote."""


def test_a_real_model_asks_for_documents_instead_of_answering_without_them(
    tmp_path: Path,
) -> None:
    """Story 12's whole subject is wording, so this is the only tier that can fail for
    the right reason: a scripted model says whatever the script says, and what is being
    tested is whether a real one, told it has nothing, declines to answer anyway.

    The greeting gets a page of its own rather than riding along as turn two. Asked
    after a turn that ended "which would you like?", a greeting is answered by picking
    that back up — which is the model being coherent, not the rule leaking into small
    talk, and it makes the assertion unable to tell the two apart."""
    at = AppTest.from_function(_page, args=(_live_app(tmp_path / "asked"),)).run()

    at.chat_input[0].set_value(IN_THE_SUBJECT).run(timeout=180)

    assert not at.exception
    answer = at.chat_message[-1].markdown[0].value.lower()
    assert any(phrase in answer for phrase in ASKS_FOR_DOCUMENTS), (
        f"an empty store was answered from model knowledge: {answer!r}"
    )
    assert _panels(at) == [], "nothing was uploaded and the answer cited something"

    greeted = AppTest.from_function(
        _page, args=(_live_app(tmp_path / "greeted"),)
    ).run()
    greeted.chat_input[0].set_value(SMALL_TALK).run(timeout=180)

    assert not greeted.exception
    greeting = greeted.chat_message[-1].markdown[0].value.lower()
    assert any(word in greeting for word in GREETS), (
        f"a greeting was not answered as a greeting: {greeting!r}"
    )
    assert _panels(greeted) == [], "a greeting cited a document"


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
    first = _holding_the_protein_doc(tmp_path)
    at = AppTest.from_function(_page, args=(first,)).run()

    at.chat_input[0].set_value(VEGETARIAN).run(timeout=180)

    assert not at.exception
    assert first.memory is not None
    kept = " ".join(fact.text.lower() for fact in first.memory.recall())
    assert "vegetarian" in kept, "the model was told something durable and dropped it"

    later = AppTest.from_function(
        _page, args=(_holding_the_protein_doc(tmp_path),)
    ).run()
    later.chat_input[0].set_value(WHAT_TO_EAT).run(timeout=180)

    assert not later.exception
    answer = later.chat_message[-1].markdown[0].value.lower()
    assert not [meat for meat in MEAT if meat in answer], (
        "a remembered constraint was in the brief and the answer ignored it"
    )


def test_a_real_model_cites_a_passage_the_reader_can_open(tmp_path: Path) -> None:
    """Story 16 against the shipped stack: a live answer's citations have to be
    clickable, and the number has to open the passage it was drawn from. The click is
    the component's own event, out of AppTest's reach — what this pins is that the
    button reaches the page and that opening its citation shows the marked passage."""
    at = AppTest.from_function(_page, args=(_holding_the_protein_doc(tmp_path),)).run()

    at.chat_input[0].set_value(IN_THE_SUBJECT).run(timeout=180)

    assert not at.exception
    [answer] = mounted_html(at, ANSWER_COMPONENT)
    assert 'data-cite="1"' in answer, f"a live answer cited nothing clickable: {answer}"

    at.session_state[OPEN_CITATION] = 1
    at.run(timeout=60)

    assert not at.exception
    assert "protein.md" in [heading.value for heading in at.header]
    [pane] = mounted_html(at, PANE_COMPONENT)
    [marked] = re.findall(r"<mark[^>]*>(.*?)</mark>", pane, re.DOTALL)
    assert "1.6" in marked, f"the cited passage is not what the pane marked: {pane}"
