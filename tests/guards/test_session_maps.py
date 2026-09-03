"""The turn drawing, checked against the turn.

The round map is read out of the source: the walk off the composition root, where the
steps are named, and the loop off the runner, where it is wired. What it can go wrong
about is a reading that finds neither — a step added to the walk and drawn nowhere, or
a loop the reader stops being able to follow.
"""

import pytest

import sequences
from cora.adapters.langgraph_runner import GATE
from cora.engine.steps import ANSWER, FOCUS, ROUTE, SCREEN, WORK
from cora.ports.graph import ASK, DONE, TOOLS


def test_the_reader_finds_the_named_steps_of_a_turn_off_the_composition_root() -> None:
    walk = sequences.walked()

    assert [name for name, _ in walk.before] == [SCREEN, ROUTE, FOCUS]
    assert walk.marker == WORK
    assert [name for name, _ in walk.after] == [ANSWER]
    assert [kind for _, kind in (*walk.before, *walk.after)] == [
        "ScreenStep",
        "RouteStep",
        "FocusStep",
        "AnswerStep",
    ]
    assert walk.loop == {
        "model": "ModelStep",
        "gate": "GateStep",
        "tools": "ToolStep",
        "ask": "AskStep",
        "router": "Router",
    }


def test_the_reader_finds_the_loop_the_runner_wires_inside_that_walk() -> None:
    plan = sequences.routing()

    assert set(plan.nodes) == {"model", GATE, TOOLS, ASK}
    assert plan.at == "model", "the round is decided where the model has just replied"
    assert plan.leaves == DONE, "and the turn leaves the loop on the one route out"
    routed = dict(plan.routes)
    assert plan.chain(routed[TOOLS]) == (GATE, TOOLS), "a round starts at the gate"
    assert plan.chain(routed[ASK]) == (ASK, GATE, TOOLS)


def test_no_path_reaches_the_tools_without_passing_the_gate() -> None:
    """The gate is unbypassable by construction rather than by discipline, and this is
    what reads that off the wiring: the round's route arrives at it, the ask's leads
    into it, and nothing else leads to the tools at all. A path that skipped it would be
    a path a later change could get an effect through without asking anyone."""
    plan = sequences.routing()

    assert [here for here, there in plan.edges if there == TOOLS] == [GATE]
    assert [route for route, target in plan.routes if target == TOOLS] == [], (
        "the router sends a round to the gate; it has no route to the tools"
    )
    assert plan.after(GATE) == TOOLS


def test_the_drawing_puts_the_rounds_between_the_steps_either_side() -> None:
    """What the page shows is the shape the story claims: screened, then the rounds
    inside the working step, then answered."""
    drawn = sequences.round_taken()
    said = [
        line.receiver
        for line in sequences.flattened(drawn.lines)
        if isinstance(line, sequences.Call)
    ]

    assert said.index(SCREEN) < said.index(WORK) < said.index("model")
    assert said.index("model") < said.index(ANSWER)


@pytest.mark.integration
def test_the_committed_map_is_what_the_generator_writes_today() -> None:
    import gen_session_maps as generator

    for path, drawing in generator.written().items():
        assert path.read_text() == drawing, f"{path.name} is behind the code it draws"
