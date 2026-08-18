from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.trace import ModelDecision, ToolUse
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react import payloads
from cora.ports.memory import Fact


def test_a_citation_carries_the_upload_its_span_was_measured_in() -> None:
    """The page reads a passage back by upload, not by filename: it is the one name
    that still points at the text the offsets were taken from."""
    citation = Citation(
        number=2, document="notes.md", start=10, end=24, upload="a1b2c3"
    )

    assert payloads.citation(citation) == {
        "number": 2,
        "document": "notes.md",
        "start": 10,
        "end": 24,
        "upload": "a1b2c3",
    }


def test_a_step_says_where_the_work_came_from() -> None:
    """The panel's origin line. A tool cora ships is the agent reaching for its own
    retrieval; anything else on offer came from the loaded plugin, which is the whole
    claim the plugin architecture makes — so the panel can say which it was."""
    core = ToolUse(name=SEARCH_TOOL_NAME, outcome="2 passages")
    remembering = ToolUse(name=REMEMBER_TOOL_NAME, outcome="kept")
    domain = ToolUse(name="training_log", outcome="3 misses")

    assert payloads.step(core)["origin"] == "core retrieval"
    assert payloads.step(remembering)["origin"] == "core retrieval"
    assert payloads.step(domain)["origin"] == "plugin tool"


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
        "origin": "core retrieval",
    }


def test_every_kind_of_step_renders_the_same_three_keys() -> None:
    """The page draws one kind of step, so a kind added to the engine arrives in the
    shape the panel already knows."""
    decision = payloads.step(ModelDecision(detail="thinking", tools=("search",)))

    assert decision == {
        "summary": "Decided to call search",
        "detail": "thinking",
        "failed": False,
        "origin": "",
    }


def test_a_result_is_the_answer_its_citations_and_its_trace() -> None:
    result = ChatResult(
        answer="Because [1].",
        citations=(Citation(number=1, document="a.txt", start=0, end=4, upload="h"),),
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
            }
        ],
        "trace": [
            {
                "summary": "Decided to call search",
                "detail": "",
                "failed": False,
                "origin": "",
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
