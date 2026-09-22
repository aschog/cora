from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session
from cora.domain.trace import ModelDecision, ToolUse
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react import payloads
from cora.ports.memory import Fact


def test_a_citation_carries_the_field_and_upload_its_span_was_measured_in() -> None:
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


def test_every_kind_of_step_renders_the_same_keys() -> None:
    decision = payloads.step(ModelDecision(detail="thinking", tools=("search",)))
    ours = payloads.step(ToolUse(name=SEARCH_TOOL_NAME, outcome="1 passage"))
    theirs = payloads.step(ToolUse(name="book_a_flight", outcome="booked"))

    assert decision == {
        "summary": "Decided to call search",
        "detail": "thinking",
        "failed": False,
        "origin": "",
        "steps": [],
    }
    assert ours["origin"] == "core tool"
    assert theirs["origin"] == "plugin tool"


def test_what_a_tool_did_inside_its_call_travels_as_the_call_s_own_steps() -> None:
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
        scopes=("cora",),
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
        "scopes": ["cora"],
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


def test_a_fact_and_a_session_carry_what_it_takes_to_act_on_them() -> None:
    assert payloads.fact(Fact(key="k1", text="No burpees.")) == {
        "key": "k1",
        "text": "No burpees.",
    }
    assert payloads.session(Session(thread_id="t1", opened_with="Why?"), "fitness") == {
        "thread_id": "t1",
        "opened_with": "Why?",
        "pin": "fitness",
    }
    # Fixed to nothing is a field named as none, rather than a key the page has to miss.
    assert payloads.session(Session(thread_id="t2", opened_with="Why?"), None) == {
        "thread_id": "t2",
        "opened_with": "Why?",
        "pin": None,
    }
