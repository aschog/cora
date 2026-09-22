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
    def __init__(self, *answers: Any) -> None:
        self.kept: dict[str, str] = {}
        self.answers = list(answers)
        self.tasks: list[str] = []
        self.shapes: list[Any] = []
        self.rounds: list[int] = []
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
        self.rounds.append(rounds)
        answered = self.answers.pop(0)
        if isinstance(answered, ToolRefusal):
            raise answered
        return answered

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        self.shown.append(did)


def _tools(cora: Cora) -> tuple[Tool, Tool]:
    return interview_tools(cora)  # ty: ignore[invalid-argument-type]


def _saving(output: FakeOutput, cora: Cora) -> Tool:
    return report_tool(output, cora)  # ty: ignore[invalid-argument-type]


def _asked(question: str) -> dict[str, Any]:
    return {"question": question}


def _running(cora: Cora) -> dict[str, Any]:
    return json.loads(cora.kept[KEPT])


def test_starting_keeps_the_setup_and_returns_the_first_question() -> None:
    cora = Cora(_asked("What is a Python decorator?"))
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
    cora = Cora(_asked("What is a decorator?"), VERDICT)
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
    cora = Cora(
        _asked("Q1?"),
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


def test_an_opening_the_loop_could_not_answer_keeps_no_interview() -> None:
    cora = Cora(ToolRefusal("the loop did not answer in the shape"))
    start, _ = _tools(cora)

    with pytest.raises(ToolRefusal):
        start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")

    assert KEPT not in cora.kept


def test_both_delegated_calls_answer_in_a_shape_with_a_round_to_correct_in() -> None:
    cora = Cora(_asked("Q1?"), VERDICT)
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")

    assert all(shape is not None for shape in cora.shapes)
    assert all(rounds > 1 for rounds in cora.rounds)


def test_a_judging_the_loop_could_not_answer_leaves_the_interview_where_it_was() -> (
    None
):
    cora = Cora(_asked("Q1?"), ToolRefusal("the loop did not answer in the shape"))
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    before = _running(cora)

    with pytest.raises(ToolRefusal):
        evaluate.run(answer="An answer.")

    assert _running(cora) == before


def test_a_second_start_over_a_judged_interview_is_refused() -> None:
    cora = Cora(_asked("Q1?"), VERDICT, _asked("Q2?"))
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")

    with pytest.raises(ToolRefusal):
        start.run(role="r", seniority="staff", difficulty="hard", interviewer="strict")

    assert len(_running(cora)["rounds"]) == 1


def test_a_start_over_an_interview_nobody_answered_runs() -> None:
    cora = Cora(_asked("Q1?"), _asked("Q2?"))
    start, _ = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")

    said = start.run(
        role="r", seniority="staff", difficulty="hard", interviewer="strict"
    )

    assert "Q2?" in said


def test_the_report_can_be_written_again_under_a_better_name() -> None:
    output = FakeOutput()
    cora = Cora(_asked("Q1?"), VERDICT)
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")
    _saving(output, cora).run(filename="mock")

    said = _saving(output, cora).run(filename="backend-mock-2")

    assert "backend-mock-2" in said


def test_saving_the_report_ends_the_interview_it_wrote() -> None:
    output = FakeOutput()
    cora = Cora(_asked("Q1?"), VERDICT, _asked("Q2?"))
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
    cora = Cora(_asked("Q1?"), VERDICT)
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
    cora = Cora(_asked("Q1?"), VERDICT)
    start, evaluate = _tools(cora)
    start.run(role="r", seniority="mid", difficulty="easy", interviewer="neutral")
    evaluate.run(answer="An answer.")

    with pytest.raises(ToolRefusal, match="letters or digits"):
        _saving(FakeOutput(), cora).run(filename="???")
