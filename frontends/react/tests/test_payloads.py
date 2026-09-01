import pytest

from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.trace import ModelDecision, ToolUse
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.plugin_set import RESERVED_TOOL_NAMES
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react import payloads
from cora.ports.memory import Fact


def test_a_citation_carries_the_field_and_upload_its_span_was_measured_in() -> None:
    """The page reads a passage back by field and upload, not by filename: together they
    are the one name that still points at the text the offsets were taken from."""
    citation = Citation(
        number=2, document="notes.md", start=10, end=24, upload="a1b2c3", scope="travel"
    )

    assert payloads.citation(citation) == {
        "number": 2,
        "document": "notes.md",
        "start": 10,
        "end": 24,
        "upload": "a1b2c3",
        "scope": "travel",
    }


def test_a_step_says_where_the_work_came_from() -> None:
    """The panel's origin line. A tool cora ships is the agent reaching for one of its
    own; anything else on offer came from the loaded plugin, which is the whole claim
    the plugin architecture makes — so the panel can say which it was.

    Driven off the engine's own list rather than a copy of it: a built-in added there
    is the one place a built-in gets added, and a page that had to be told separately
    would go on calling it a plugin's."""
    for name in RESERVED_TOOL_NAMES:
        assert payloads.step(ToolUse(name=name))["origin"] == "core tool"

    domain = ToolUse(name="training_log", outcome="3 misses")
    assert domain.name not in RESERVED_TOOL_NAMES
    assert payloads.step(domain)["origin"] == "plugin tool"


def test_a_built_in_the_engine_gains_is_not_reported_as_a_plugin_s(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reason it reads the engine's list instead of holding its own: a third
    built-in gets registered where collisions are already checked, and a copy here
    would go on labelling it `plugin tool` — the page lying about the one thing the
    plugin architecture exists to show."""
    monkeypatch.setitem(RESERVED_TOOL_NAMES, "summarise_document", "summaries")

    shipped = ToolUse(name="summarise_document", outcome="one paragraph")

    assert payloads.step(shipped)["origin"] == "core tool"


def test_a_step_that_called_no_tool_claims_no_origin() -> None:
    """A decision is cora's own, so the line has nothing to say and is not drawn."""
    assert payloads.step(ModelDecision(tools=("search",)))["origin"] == ""


def test_a_tool_step_renders_summary_detail_and_failure() -> None:
    step = ToolUse(
        name="search_documents",
        arguments={"query": "squats"},
        outcome="2 passages",
        detail="…",
        failed=False,
    )

    assert payloads.step(step) == {
        "summary": 'search_documents(query="squats") → 2 passages',
        "detail": "…",
        "failed": False,
        "origin": "core tool",
        "steps": [],
    }


def test_every_kind_of_step_renders_the_same_keys() -> None:
    """The page draws one kind of step, so a kind added to the engine arrives in the
    shape the panel already knows."""
    decision = payloads.step(ModelDecision(detail="thinking", tools=("search",)))

    assert decision == {
        "summary": "Decided to call search",
        "detail": "thinking",
        "failed": False,
        "origin": "",
        "steps": [],
    }


def test_what_a_tool_did_inside_its_call_travels_as_the_call_s_own_steps() -> None:
    """A plugin's tool may run a turn of its own, and the wire carries that work under
    the call rather than losing it on the way to the page."""
    call = payloads.step(
        ToolUse(
            name="research",
            outcome="answered",
            steps=(ModelDecision(tools=("search_documents",)),),
        )
    )

    assert [inside["summary"] for inside in call["steps"]] == [
        "Decided to call search_documents"
    ]


def test_a_result_is_the_answer_its_citations_and_its_trace() -> None:
    result = ChatResult(
        answer="Because [1].",
        citations=(
            Citation(
                number=1, document="a.txt", start=0, end=4, upload="h", scope="cora"
            ),
        ),
        trace=(ModelDecision(tools=("search",)),),
    )

    assert payloads.result(result) == {
        "answer": "Because [1].",
        "citations": [
            {
                "number": 1,
                "document": "a.txt",
                "start": 0,
                "end": 4,
                "upload": "h",
                "scope": "cora",
            }
        ],
        "trace": [
            {
                "summary": "Decided to call search",
                "detail": "",
                "failed": False,
                "origin": "",
                "steps": [],
            }
        ],
    }


def test_a_turn_is_a_question_and_the_result_it_got() -> None:
    """A reopened conversation redraws from the shape a fresh answer arrives in."""
    turn = Turn(question="Why?", result=ChatResult(answer="Because."))

    assert payloads.turn(turn) == {
        "question": "Why?",
        "result": {"answer": "Because.", "citations": [], "trace": []},
    }


def test_a_fact_and_a_session_carry_what_it_takes_to_act_on_them() -> None:
    """A key forgets a fact; a thread id reopens a conversation."""
    assert payloads.fact(Fact(key="k1", text="No burpees.")) == {
        "key": "k1",
        "text": "No burpees.",
    }
    assert payloads.session(Session(thread_id="t1", opened_with="Why?")) == {
        "thread_id": "t1",
        "opened_with": "Why?",
    }


def test_the_origin_of_a_built_in_names_no_act_only_one_of_them_performs() -> None:
    """The list holds two built-ins and they do different things: one searches the
    documents, the other writes down what cora keeps about the user. One label over
    both can only be what they have in common — naming the search tells the reader that
    a memory write went through their documents. What the tool *did* is the step's own
    summary, which says so in its own words."""
    searched = payloads.step(ToolUse(name=SEARCH_TOOL_NAME))["origin"]
    kept = payloads.step(ToolUse(name=REMEMBER_TOOL_NAME, outcome="noted"))["origin"]

    assert searched == kept
    assert "retrieval" not in kept and "search" not in kept
