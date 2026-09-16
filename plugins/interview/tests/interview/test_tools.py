import json
from typing import Any

import pytest

from cora.plugins.interview.tools import (
    KEPT,
    START_SCHEMA,
    interview_tools,
    report_tool,
)
from cora.ports.plugin import Tool, ToolRefusal
from fakes import FakeOutput

VERDICT: dict[str, Any] = {
    "correctness": 4,
    "structure": 4,
    "communication": 4,
    "feedback": "The right idea, clearly put, and concise with it.",
    "next_question": "What does the GIL rule out?",
}


class Cora:
    """The host the tools keep the interview on, with the delegated loop scripted."""

    def __init__(self, *answers: Any) -> None:
        self.kept: dict[str, str] = {}
        self.answers = list(answers)
        self.tasks: list[str] = []
        self.shapes: list[Any] = []
        self.shown: list[str] = []

    @property
    def state(self) -> "Cora":
        return self

    def read(self, name: str) -> str | None:
        return self.kept.get(name)

    def keep(self, name: str, value: str | None) -> None:
        if value is None:
            self.kept.pop(name, None)
        else:
            self.kept[name] = value

    def delegate(
        self,
        task: str,
        tools: tuple[Any, ...] = (),
        rounds: int = 3,
        *,
        shape: Any = None,
    ) -> Any:
        self.tasks.append(task)
        self.shapes.append(shape)
        return self.answers.pop(0)

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        self.shown.append(did)


def _tools(cora: Cora) -> tuple[Tool, Tool]:
    return interview_tools(cora)  # ty: ignore[invalid-argument-type]


def _saving(output: FakeOutput, cora: Cora) -> Tool:
    return report_tool(output, cora)  # ty: ignore[invalid-argument-type]


def _running(cora: Cora) -> dict[str, Any]:
    return json.loads(cora.kept[KEPT])


def test_starting_keeps_the_setup_and_returns_the_first_question() -> None:
    cora = Cora("What is a Python decorator?")
    start, _ = _tools(cora)

    said = start.run(
        role="backend engineer",
        seniority="senior",
        difficulty="hard",
        interviewer="strict",
    )

    assert "What is a Python decorator?" in said
    held = _running(cora)
    assert held["question"] == "What is a Python decorator?"
    assert held["rounds"] == []
    assert "backend engineer" in cora.tasks[0]
    assert "strict" in cora.tasks[0]


def test_the_card_asks_for_what_is_missing_and_offers_a_way_off() -> None:
    """The card is built from the schema the tool already declared, carrying what the
    conversation settled, and cannot be sent until the rest is filled in."""
    start, _ = _tools(Cora())
    assert start.asks is not None

    card = start.asks({"role": "data analyst"})

    assert card is not None
    named = {field.name: field for field in card.fields}
    assert set(named) == set(START_SCHEMA["required"])
    assert named["role"].value == "data analyst"
    assert named["difficulty"].schema["enum"] == ["easy", "medium", "hard"]
    starting, leaving = card.actions
    assert starting.needs_valid
    assert starting.answer is not None
    assert leaving.answer is None


def test_a_call_with_everything_settled_runs_as_called() -> None:
    start, _ = _tools(Cora())
    assert start.asks is not None

    asked = start.asks(
        {
            "role": "r",
            "seniority": "mid",
            "difficulty": "easy",
            "interviewer": "friendly",
        }
    )

    assert asked is None


def test_an_answer_before_any_interview_is_refused() -> None:
    _, evaluate = _tools(Cora())

    with pytest.raises(ToolRefusal, match="Start one"):
        evaluate.run(answer="STAR, obviously.")


def test_a_judged_answer_is_kept_scored_and_the_question_advances() -> None:
    cora = Cora("What is a decorator?", VERDICT)
    start, evaluate = _tools(cora)
    start.run(
        role="backend engineer",
        seniority="senior",
        difficulty="hard",
        interviewer="strict",
    )

    said = evaluate.run(answer="A callable wrapping a callable.")

    assert VERDICT["feedback"] in said
    assert "12/15" in said
    held = _running(cora)
    [judged] = held["rounds"]
    assert judged["question"] == "What is a decorator?"
    assert judged["answer"] == "A callable wrapping a callable."
    assert judged["score"] == 12
    assert held["question"] == "What does the GIL rule out?"
    assert any("judged answer 1: 12/15" in line for line in cora.shown)


def test_the_next_question_carries_nothing_the_judge_wrote_around_it() -> None:
    """The scores and the question are read off a shape the loop answered in, so the
    order the judge wrote them in, and anything it added after, are not the plugin's
    to parse — and never end up inside the question the user is asked next."""
    cora = Cora(
        "Q1?",
        {
            "correctness": 4,
            "structure": 4,
            "communication": 4,
            "feedback": "The right idea, clearly put.",
            "next_question": "What does the GIL rule out?",
        },
    )
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")

    evaluate.run(answer="An answer.")

    held = _running(cora)
    assert held["question"] == "What does the GIL rule out?"
    assert held["rounds"][0]["score"] == 12


def test_a_second_start_over_a_judged_interview_is_refused() -> None:
    """The transcript is the thing the user was promised they could keep, and a model
    asked for "the same again, but as a staff engineer" calls start, not save."""
    cora = Cora("Q1?", VERDICT, "Q2?")
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")

    with pytest.raises(ToolRefusal):
        start.run(role="r", seniority="staff", difficulty="hard", interviewer="strict")

    assert len(_running(cora)["rounds"]) == 1


def test_a_start_over_an_interview_nobody_answered_runs() -> None:
    """Nothing is lost by restarting one that was never answered, and a user who
    misread the card would otherwise be stuck with the interview it started."""
    cora = Cora("Q1?", "Q2?")
    start, _ = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")

    said = start.run(
        role="r", seniority="staff", difficulty="hard", interviewer="strict"
    )

    assert "Q2?" in said


def test_saving_the_report_ends_the_interview_it_wrote() -> None:
    """The report is what the interview was for: once it is on disk the next start is
    a new interview rather than a refusal the user cannot get past."""
    output = FakeOutput()
    cora = Cora("Q1?", VERDICT, "Q2?")
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")

    _saving(output, cora).run(filename="report.md")

    assert _saving(output, cora)
    said = start.run(
        role="r", seniority="staff", difficulty="hard", interviewer="strict"
    )
    assert "Q2?" in said


def test_the_report_writes_every_round_and_says_where_it_went() -> None:
    output = FakeOutput()
    cora = Cora("Q1?", VERDICT)
    start, evaluate = _tools(cora)
    start.run(
        role="backend engineer",
        seniority="senior",
        difficulty="hard",
        interviewer="strict",
    )
    evaluate.run(answer="A callable wrapping a callable.")

    said = _saving(output, cora).run(filename="Backend mock #1")

    [(name, kept)] = output.written.items()
    assert name.startswith("backend-mock-1-")
    assert name.endswith(".md")
    assert "Q1?" in kept
    assert "A callable wrapping a callable." in kept
    assert "12/15" in kept
    assert f"/kept/{name}" in said


def test_a_report_before_any_judged_answer_is_refused() -> None:
    with pytest.raises(ToolRefusal, match="no report"):
        _saving(FakeOutput(), Cora()).run(filename="empty")


def test_a_filename_of_no_letters_or_digits_is_refused() -> None:
    cora = Cora("Q1?", VERDICT)
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")

    with pytest.raises(ToolRefusal, match="letters or digits"):
        _saving(FakeOutput(), cora).run(filename="???")
