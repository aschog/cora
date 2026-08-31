"""How often the router puts a question in the right field, against a real model.

The `llm` tier, so it is hand-run and costs money. The subject is the routing step
alone rather than a whole turn: what is measured is a reading of one question, and
paying for an answer to each would measure the answer instead.

The recorded set holds questions asked on their own and questions phrased as
follow-ups. An unpinned thread is routed every turn, and the router is deliberately
given the question without the thread — so a follow-up that no longer names its
subject is the case most likely to go wrong. A question read as two fields counts as a
miss: the running app stops and asks, which is right, and is not a field.
"""

import dataclasses
from pathlib import Path

import pytest

from cora.app.assembly import build
from cora.engine.steps import RouteStep
from cora.ports.host import DEFAULT_SCOPE
from live import live_config

pytestmark = pytest.mark.llm

FITNESS, TRAVEL = "fitness", "travel"
SCOPED_PLUGINS = (
    "cora.plugins.security",
    "cora.plugins.fitness",
    "cora.plugins.travel",
)

RECORDED: tuple[tuple[str, str], ...] = (
    # Asked on their own.
    ("How much protein should I eat per kg of bodyweight?", FITNESS),
    ("Is a 5x5 programme enough for a beginner?", FITNESS),
    ("My squat has stalled for three weeks — what should I change?", FITNESS),
    ("What is my daily energy expenditure at 78 kg?", FITNESS),
    ("How early should I book a sleeper across Europe?", TRAVEL),
    ("What should I pack for a week in one carry-on?", TRAVEL),
    ("Which Lisbon neighbourhood is quietest to stay in?", TRAVEL),
    ("Do I need a seat reservation if I already have a rail pass?", TRAVEL),
    # Phrased as follow-ups, with nothing naming the subject but the wording.
    ("And how early should I book that?", TRAVEL),
    ("How many sets, then?", FITNESS),
    ("What about the connection times?", TRAVEL),
    ("Should I deload instead?", FITNESS),
    ("Is the sleeper worth it over a hotel night?", TRAVEL),
    ("Would more volume help?", FITNESS),
    # Belonging to neither, so answered plainly.
    ("What are you, and what can you do?", DEFAULT_SCOPE),
    ("Summarise the document I uploaded yesterday.", DEFAULT_SCOPE),
)
"""Every question, with the field it belongs to. Grown rather than rewritten: a case
removed after a bad run would make the number say what the set was chosen to say."""

THRESHOLD = 0.75
"""The share the router has to reach.

Not yet measured: this is a floor to run the set against, replaced by the first real
number the tier reports. Raised only against a measurement — a threshold set above what
was ever observed fails the tier on the model rather than on a regression.
"""


def _router(store: Path) -> RouteStep:
    """The shipped router, off the walk the composition root wired.

    Taken from the app rather than built here: the prompt, the model and the outlines it
    chooses between are what cora actually ships, and a router assembled by the test
    would measure the test's wiring.
    """
    runner = build(live_config(store, SCOPED_PLUGINS, (FITNESS, TRAVEL))).agent.runner
    _, route, _ = runner.before  # ty: ignore[unresolved-attribute]
    step = route.take
    assert isinstance(step, RouteStep)
    # A question read as two fields stops the run to ask, which cannot happen outside a
    # graph — declining is what makes such a case a miss rather than an error.
    return dataclasses.replace(step, pause=lambda decision: None)


def _chose(step: RouteStep, question: str) -> str:
    settled = step({"question": question})["scopes"]
    return settled[0] if len(settled) == 1 else ", ".join(settled)


def test_the_router_chooses_the_right_field_often_enough(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The number, and the cases behind it. Printed rather than only asserted: a share
    over the bar with the same two cases failing every run is a set that has stopped
    measuring anything, and only the listing shows that."""
    step = _router(tmp_path)

    chosen = [
        (question, wanted, _chose(step, question)) for question, wanted in RECORDED
    ]

    right = [case for case in chosen if case[1] == case[2]]
    share = len(right) / len(chosen)
    with capsys.disabled():
        print(f"\nrouting: {len(right)}/{len(chosen)} = {share:.0%}")
        for question, wanted, got in chosen:
            mark = " " if wanted == got else "✗"
            print(f" {mark} {wanted:>8} ← {got:<8} {question}")
    assert share >= THRESHOLD, f"the router chose {share:.0%}, under {THRESHOLD:.0%}"
