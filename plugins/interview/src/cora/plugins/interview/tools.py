"""The mock interview: started on a card, judged answer by answer, kept as a file."""

import hashlib
import json
import re
from typing import Any

from cora.domain.card import ActionOffered, Card, fields_of, missing_from
from cora.ports.host import Host
from cora.ports.output import Output
from cora.ports.plugin import Tool, ToolRefusal

KEPT = "interview"
"""Where the running interview lives in the conversation's state: the setup, the
question on the table, and every judged round so far, as one JSON object."""

START_TOOL_NAME = "start_mock_interview"
START_TOOL_DESCRIPTION = (
    "Start a mock interview: the user picks the role, the seniority, the difficulty "
    "and the interviewer's manner, and the first question comes back. Whatever the "
    "conversation has not settled, the user is asked for on a card."
)
START_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "role": {
            "type": "string",
            "description": "The position interviewed for, e.g. 'backend engineer'.",
        },
        "seniority": {"type": "string", "enum": ["junior", "mid", "senior", "staff"]},
        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
        "interviewer": {"type": "string", "enum": ["strict", "neutral", "friendly"]},
    },
    "required": ["role", "seniority", "difficulty", "interviewer"],
    "additionalProperties": False,
}

EVALUATE_TOOL_NAME = "evaluate_answer"
EVALUATE_TOOL_DESCRIPTION = (
    "Judge the user's answer to the current mock-interview question against a rubric "
    "— correctness, structure, communication — and get the verdict and the next "
    "question back. Call it on every answer given during a mock interview."
)
EVALUATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "The user's answer to the question on the table, verbatim.",
        }
    },
    "required": ["answer"],
    "additionalProperties": False,
}

REPORT_TOOL_NAME = "save_interview_report"
REPORT_TOOL_DESCRIPTION = (
    "Save the mock interview run in this conversation — every question, answer and "
    "verdict, with the running score — as a Markdown file the user keeps. Offer it "
    "when the interview is over; the user approves the save before it happens."
)
REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "filename": {
            "type": "string",
            "description": "What to call the report file, e.g. 'backend-mock-1'.",
        }
    },
    "required": ["filename"],
    "additionalProperties": False,
}

NOT_STARTED = (
    "No mock interview is running in this conversation. Start one with "
    "start_mock_interview first."
)
NOTHING_TO_REPORT = (
    "No answers have been judged in this conversation, so there is no report to "
    "save. Run a mock interview first."
)
UNNAMEABLE = (
    "'{filename}' leaves nothing behind once it is made safe to write; give the "
    "report a filename with some letters or digits in it"
)

CARD_PROMPT = "Tell me about the interview to run, and I'll play the interviewer."
START_LABEL = "Start the interview"
NOT_NOW = "Not now"
NOT_STARTING = "No interview, then."

OPENING = (
    "Open a {difficulty} mock interview for a {seniority} {role}, in the manner of "
    "a {interviewer} interviewer. Search the documents for a job description or CV "
    "and aim the question at what you find; with none there, ask a standard opening "
    "question for the role. Answer with the question alone — no preamble."
)
JUDGING = (
    "You are a {interviewer} interviewer judging one answer in a {difficulty} mock "
    "interview for a {seniority} {role}.\n\n"
    "Question: {question}\n"
    "Candidate's answer: {answer}\n\n"
    "Score the answer 1-5 on each of correctness, structure and communication, with "
    "one sentence of feedback per criterion. Then finish with exactly these two "
    "lines:\n"
    "TOTAL: <the three scores added up>/15\n"
    "NEXT QUESTION: <one new {difficulty} question that follows on from this answer>"
)

OPENING_ROUNDS = 2
"""One lookup for an uploaded job description, and the round writing the question."""
JUDGING_ROUNDS = 1
"""A verdict needs no lookup, so the judge gets one round to write it."""

MOST = 15
_TOTAL = re.compile(r"TOTAL:\s*(\d{1,2})\s*/\s*15")
_NEXT = re.compile(r"NEXT QUESTION:\s*(.+)", re.DOTALL)

UNSAFE = re.compile(r"[^a-z0-9]+")
HASH_LENGTH = 12
SUFFIX = ".md"


def interview_tools(cora: Host) -> tuple[Tool, Tool]:
    """The interview itself, closed over the host that keeps it between turns.

    Both tools answer with what a delegated loop wrote, so both are declared
    untrusted: the documents went into it, and its words are not cora's own.
    """

    def start(role: str, seniority: str, difficulty: str, interviewer: str) -> str:
        question = cora.delegate(
            OPENING.format(
                role=role,
                seniority=seniority,
                difficulty=difficulty,
                interviewer=interviewer,
            ),
            rounds=OPENING_ROUNDS,
        )
        cora.state.keep(
            KEPT,
            json.dumps(
                {
                    "role": role,
                    "seniority": seniority,
                    "difficulty": difficulty,
                    "interviewer": interviewer,
                    "question": question,
                    "rounds": [],
                }
            ),
        )
        cora.show(f"started a {difficulty} {role} interview", detail=question)
        return f"The interview is on. First question:\n\n{question}"

    def evaluate(answer: str) -> str:
        held = cora.state.read(KEPT)
        if held is None:
            raise ToolRefusal(NOT_STARTED)
        interview = json.loads(held)
        verdict = cora.delegate(
            JUDGING.format(answer=answer, **interview), rounds=JUDGING_ROUNDS
        )
        score = _score(verdict)
        follow = _NEXT.search(verdict)
        interview["rounds"].append(
            {
                "question": interview["question"],
                "answer": answer,
                "verdict": verdict,
                "score": score,
            }
        )
        if follow:
            interview["question"] = follow.group(1).strip()
        cora.state.keep(KEPT, json.dumps(interview))
        judged = len(interview["rounds"])
        said = f"{score}/{MOST}" if score is not None else "unscored"
        cora.show(f"judged answer {judged}: {said}", detail=verdict)
        return verdict

    return (
        Tool(
            name=START_TOOL_NAME,
            description=START_TOOL_DESCRIPTION,
            parameter_schema=START_SCHEMA,
            run=start,
            untrusted=True,
            asks=_asks,
        ),
        Tool(
            name=EVALUATE_TOOL_NAME,
            description=EVALUATE_TOOL_DESCRIPTION,
            parameter_schema=EVALUATE_SCHEMA,
            run=evaluate,
            untrusted=True,
        ),
    )


def _asks(arguments: dict[str, Any]) -> Card | None:
    if not missing_from(START_SCHEMA, arguments):
        return None
    return Card(
        prompt=CARD_PROMPT,
        fields=fields_of(START_SCHEMA, arguments),
        actions=(
            ActionOffered(
                label=START_LABEL,
                answer="Start",
                needs_valid=True,
                settled="Starting the interview.",
            ),
            ActionOffered(label=NOT_NOW, answer=None, settled=NOT_STARTING),
        ),
    )


def report_tool(output: Output, cora: Host) -> Tool:
    """The one tool here that changes something outside cora, bound to the one place
    this deployment lets an effect write — which is why it is declared as having one,
    and why a call of it waits for the user."""

    def save(filename: str) -> str:
        held = cora.state.read(KEPT)
        if held is None:
            raise ToolRefusal(NOTHING_TO_REPORT)
        interview = json.loads(held)
        if not interview["rounds"]:
            raise ToolRefusal(NOTHING_TO_REPORT)
        kept = _written(interview)
        where = output.write(_filename(filename, kept), kept)
        return f"Saved the interview report to {where}"

    return Tool(
        name=REPORT_TOOL_NAME,
        description=REPORT_TOOL_DESCRIPTION,
        parameter_schema=REPORT_SCHEMA,
        run=save,
        effect=True,
    )


def _score(verdict: str) -> int | None:
    found = _TOTAL.search(verdict)
    if found is None:
        return None
    return min(int(found.group(1)), MOST)


def _written(interview: dict[str, Any]) -> str:
    rounds = interview["rounds"]
    scored = [each["score"] for each in rounds if each["score"] is not None]
    total = (
        f"{sum(scored)}/{MOST * len(scored)} over {len(scored)} scored answers"
        if scored
        else "unscored"
    )
    lines = [
        f"# Interview report: {interview['role']}",
        "",
        f"**{interview['seniority']}, {interview['difficulty']}, "
        f"{interview['interviewer']} interviewer** — {total}",
        "",
    ]
    for number, each in enumerate(rounds, start=1):
        lines.extend(
            [
                f"## Question {number}",
                "",
                each["question"],
                "",
                f"**Answer:** {each['answer']}",
                "",
                each["verdict"],
                "",
            ]
        )
    return "\n".join(lines)


def _filename(filename: str, kept: str) -> str:
    """The asked-for name as a filename, with the head of the report hashed onto it.

    Made rather than taken, because the name is the model's prose — a slash in it is
    a word to the model and a path to a filesystem. The hash is of the text, so the
    same report saved twice is one file and a longer interview saved again is a
    second: nothing the user approved is written over.

    Raises:
        ToolRefusal: Nothing is left of the name once it is safe to write.
    """
    stem = UNSAFE.sub("-", filename.lower().removesuffix(SUFFIX)).strip("-")
    if not stem:
        raise ToolRefusal(UNNAMEABLE.format(filename=filename))
    marked = hashlib.sha256(kept.encode()).hexdigest()[:HASH_LENGTH]
    return f"{stem}-{marked}{SUFFIX}"
