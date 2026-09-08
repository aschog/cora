"""The tests that run the whole shipped stack against a real model: the real
composition root, the real store and embedder, OpenRouter over the network, and
the shell's HTTP surface driven the way the page drives it. They are the only cover for
behaviour a stub cannot show — a scripted model answers however the script says, so it
can never reveal the model ignoring an instruction. Since story 15 removed the grounding
gate, these are the only tests that can catch a model answering a document question from
what it happens to know.
"""

import re
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from cora.app.assembly import App, build
from cora.domain.card import Answer
from cora.domain.decision import TurnPaused
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.plugins.fitness.tools import DAILY_ENERGY_TOOL
from live import live_config
from sse import frames

pytestmark = pytest.mark.llm

PROTEIN_DOC = b"""# Protein

For strength training, aim for 1.6 to 2.2 g of protein per kg of bodyweight per day.
Spread it over three or four meals.
"""
IN_THE_SUBJECT = "How much protein should I eat per kg of bodyweight?"
LIVE_PLUGINS = ("cora.plugins.security", "cora.plugins.fitness")


def _live_app(store: Path) -> App:
    """The shipped composition root, pointed at stores of its own. Every other default
    is the deployed one — the model, the preamble and the reminder under test are
    whatever cora actually ships."""
    return build(live_config(store, LIVE_PLUGINS))


def _holding_the_protein_doc(store: Path) -> App:
    """Indexed behind the page's back, for the tests whose subject starts at the
    question. The happy path uploads the same document over the API instead."""
    app = _live_app(store)
    app.knowledge_base.add_file(PROTEIN_DOC, "protein.md")
    return app


def _page(app: App) -> TestClient:
    """The surface the page reads, with the plugins the deployment configured. No
    timeout to set: the app runs in this process, so a live turn takes as long as the
    model takes rather than as long as a socket allows."""
    return TestClient(api(app))


def _turn(page: TestClient, question: str, thread: str = "acceptance") -> dict:
    """One turn as the page receives it: the frames the stream carried, of which the
    last is the turn itself. A turn that failed carries no answer, and reads as the
    error frame the page would draw — this tier is run by hand, so a check that fails
    has to be able to say why."""
    streamed = frames(
        page.post("/api/ask", json={"question": question, "thread_id": thread}).text
    )
    name, data = streamed[-1]
    assert name == "turn", f"the turn did not finish: {streamed[-1]}"
    return data


def _opens_a_passage(turn: dict) -> bool:
    """What the Sources panel used to prove, and more: the reader has a citation to
    open. Read off the citations rather than the text, because a number the domain never
    resolved — glued to a word, or belonging to no registered passage — reaches the page
    as text and opens nothing."""
    return turn["citations"] != []


def _steps(turn: dict) -> str:
    return "\n".join(f"{step['summary']}\n{step['detail']}" for step in turn["trace"])


def _documents(page: TestClient) -> list[str]:
    return page.get("/api/documents").json()


def _remembered(page: TestClient) -> str:
    return " ".join(fact["text"].lower() for fact in page.get("/api/memory").json())


UPLOADED = {"file": ("protein.md", PROTEIN_DOC, "text/markdown")}
NEEDS_THE_CALCULATOR = (
    "I'm a 34-year-old man, 80 kg at 180 cm, training hard four times a week. "
    "What is my total daily energy expenditure?"
)
KEEP_THIS = "Remember that I'm vegetarian."
FAILED = "⚠️"


def test_a_whole_session_uploads_asks_calculates_and_remembers(tmp_path: Path) -> None:
    """The demo as one conversation on one thread: the document goes in through the
    upload the page posts, the answer comes back cited from it, the calculation goes to
    the plugin's tool instead of the model's arithmetic, and a fact the user asks it to
    keep reaches the store the memory panel reads."""
    app = _live_app(tmp_path)
    with _page(app) as page:
        added = page.post("/api/documents", files=UPLOADED)  # the embedder loads here

        assert added.status_code == 200, added.text
        assert added.json() == {"document": "protein.md", "chunks": 1}
        assert _documents(page) == ["protein.md"]

        asked = _turn(page, IN_THE_SUBJECT)

        assert _opens_a_passage(asked), (
            f"the answer rests on no passage the reader can open: {asked['answer']!r}"
        )
        assert f"{SEARCH_TOOL_NAME}(" in _steps(asked)
        assert "protein.md" in _steps(asked), "the search never reached the document"

        calculated = _steps(_turn(page, NEEDS_THE_CALCULATOR))

        assert f"{DAILY_ENERGY_TOOL.name}(" in calculated, (
            "the model did the arithmetic itself instead of calling the plugin's tool"
        )
        assert FAILED not in calculated

        assert f"{REMEMBER_TOOL_NAME}(" in _steps(_turn(page, KEEP_THIS))
        assert app.memory is not None
        kept = " ".join(fact.text.lower() for fact in app.memory.recall())
        assert "vegetarian" in kept
        assert "vegetarian" in _remembered(page)


"""The greeting is checked for *being a greeting*, which is all story 12 claims for it.
An empty store is a fact about the app, and a real model volunteers it while greeting —
"nice to meet you; I don't have any documents from you yet, how can I help?" is small
talk answered as small talk, so an assertion that no upload is ever mentioned would be
testing a rule nobody wrote."""


def test_a_real_model_cites_a_passage_the_reader_can_open(tmp_path: Path) -> None:
    """Story 16 against the shipped stack: a live answer's citations have to be
    openable, and the number has to lead back to the passage it was drawn from. The
    click is the page's own event — what this pins is that the citation reaches the
    page with the span it was measured in, and that the span holds what was cited."""
    with _page(_holding_the_protein_doc(tmp_path)) as page:
        turn = _turn(page, IN_THE_SUBJECT)

        assert _opens_a_passage(turn), (
            f"a live answer cited nothing: {turn['answer']!r}"
        )
        [cited, *_] = turn["citations"]
        assert cited["document"] == "protein.md"
        opened = page.get(f"/api/uploads/{cited['upload']}")

        assert opened.status_code == 200, opened.text
        passage = opened.json()["text"][cited["start"] : cited["end"]]
        assert "1.6" in passage, (
            f"the cited span is not what was answered from: {passage!r}"
        )


CONFLICTING = (
    "bodyweight 77 kg, from the intake form on 17 August",
    "bodyweight 75 kg, from the coach notes in February",
    "bodyweight 85 kg, from the physio letter",
)
NEEDS_A_WEIGHT = "What is my basal metabolic rate?"
DECIDING = "llm-decision"


def test_a_real_model_asks_which_value_to_use_instead_of_picking_one(
    tmp_path: Path,
) -> None:
    """The honest proof that the pause is the model's decision: nothing in the question
    mentions bodyweight or asks to be asked, and no script offers the options. Three
    values for one fact are in memory, and the question depends on it — a model that
    guesses answers straight through, and one that reads them stops."""
    app = _live_app(tmp_path)
    assert app.memory is not None
    for fact in CONFLICTING:
        app.memory.remember(fact)

    with pytest.raises(TurnPaused) as stopped:
        app.agent.answer(NEEDS_A_WEIGHT, DECIDING)

    card = stopped.value.pending.card
    offered = " ".join(action.label for action in card.actions)
    assert {"77", "75", "85"} <= set(re.findall(r"\d+", offered)), (
        f"the model asked about something other than the three it holds: {card}"
    )

    answered = app.agent.resume(Answer(action="75 kg"), DECIDING)

    assert answered.answer.strip(), "the resumed turn came back with nothing"
    rested_on = answered.answer + " ".join(step.summary for step in answered.trace)
    assert "75" in rested_on, (
        f"the answer does not rest on the value chosen: {rested_on!r}"
    )
