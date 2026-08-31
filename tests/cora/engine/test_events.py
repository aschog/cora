"""What a handler's return means at each point in a turn."""

import pytest

from cora.domain.errors import InputRejectedError
from cora.domain.trace import TraceStep
from cora.engine.events import UNCHECKED, UNSCREENED, dispatch
from cora.ports.host import (
    BRIEFING,
    CALLING,
    HANDLER,
    SCREENING,
    Handler,
    Registration,
    Subscription,
)
from cora.ports.plugin import ToolRefusal

FIRST = "fixture_plugins.first"
SECOND = "fixture_plugins.second"


def _subscribed(module: str, event: str, handle: Handler) -> Registration:
    return Registration(
        module=module, kind=HANDLER, value=Subscription(event=event, handle=handle)
    )


def _breaks(_: object) -> str:
    raise RuntimeError("the secret is hunter2")


def test_a_refusal_comes_back_as_the_events_own_exception() -> None:
    trace: list[TraceStep] = []

    with pytest.raises(InputRejectedError) as refused:
        dispatch(
            SCREENING,
            "anything",
            (_subscribed(FIRST, SCREENING, lambda question: "no shouting"),),
            trace,
        )

    assert refused.value.user_message == "no shouting"
    assert [step.summary for step in trace] == [f"{FIRST} refused the question"]


def test_a_refused_call_is_raised_as_a_tool_refuses() -> None:
    """Which is the path a refusing tool already has, so the turn answers anyway."""
    with pytest.raises(ToolRefusal, match="not today"):
        dispatch(
            CALLING,
            object(),
            (_subscribed(FIRST, CALLING, lambda call: "not today"),),
            [],
        )


def test_a_handler_that_returns_nothing_lets_the_value_through() -> None:
    trace: list[TraceStep] = []

    admitted = dispatch(
        SCREENING,
        "a question",
        (_subscribed(FIRST, SCREENING, lambda question: None),),
        trace,
    )

    assert admitted == "a question"
    assert trace == [], "a handler that did nothing is not a step"


def test_amendments_chain_in_order_and_the_trace_names_each_plugin() -> None:
    trace: list[TraceStep] = []

    amended = dispatch(
        BRIEFING,
        "cora",
        (
            _subscribed(FIRST, BRIEFING, lambda brief: f"{brief}, then first"),
            _subscribed(SECOND, BRIEFING, lambda brief: f"{brief}, then second"),
        ),
        trace,
    )

    assert amended == "cora, then first, then second"
    assert [step.summary for step in trace] == [
        f"{FIRST} amended the brief",
        f"{SECOND} amended the brief",
    ]


def test_an_observer_sees_the_value_and_changes_nothing() -> None:
    seen: list[str] = []

    unchanged = dispatch(
        BRIEFING, "cora", (_subscribed(FIRST, BRIEFING, seen.append),), []
    )

    assert (unchanged, seen) == ("cora", ["cora"])


def test_an_amender_that_raises_is_dropped_and_the_next_one_still_runs() -> None:
    trace: list[TraceStep] = []

    amended = dispatch(
        BRIEFING,
        "cora",
        (
            _subscribed(FIRST, BRIEFING, _breaks),
            _subscribed(SECOND, BRIEFING, lambda brief: f"{brief}, then second"),
        ),
        trace,
    )

    assert amended == "cora, then second"
    broke, ran = trace
    assert broke.failed and not ran.failed
    assert "RuntimeError" in broke.detail
    assert "hunter2" not in broke.detail


@pytest.mark.parametrize(
    ("event", "raised", "reason"),
    [(SCREENING, InputRejectedError, UNSCREENED), (CALLING, ToolRefusal, UNCHECKED)],
)
def test_a_refusing_handler_that_raises_refuses_anyway(
    event: str, raised: type[Exception], reason: str
) -> None:
    """A broken rule must not admit an input, and what it was holding stays out of what
    is passed on: only the kind of what it raised is said."""
    with pytest.raises(raised) as refused:
        dispatch(event, "anything", (_subscribed(FIRST, event, _breaks),), [])

    assert str(refused.value) == reason
    assert "hunter2" not in str(refused.value)


def test_an_amendment_of_the_wrong_shape_is_dropped_like_a_raise() -> None:
    """Failing open means a plugin cannot cost the turn: a brief handed back as a
    dictionary would end it as surely as an exception would."""
    trace: list[TraceStep] = []

    amended = dispatch(
        BRIEFING,
        "cora",
        (_subscribed(FIRST, BRIEFING, lambda brief: {"brief": brief}),),
        trace,
    )

    assert amended == "cora"
    [dropped] = trace
    assert dropped.failed
    assert "dict" in dropped.detail


def test_a_refusal_that_is_not_a_sentence_still_refuses_and_says_nothing_of_it() -> (
    None
):
    """Fail closed: a handler answering with something that is not a reason has refused
    all the same, and what the user reads is cora's wording rather than a repr."""
    trace: list[TraceStep] = []

    with pytest.raises(InputRejectedError) as refused:
        dispatch(
            SCREENING,
            "anything",
            (_subscribed(FIRST, SCREENING, lambda q: True),),
            trace,
        )

    assert refused.value.user_message == UNSCREENED
    [named] = trace
    assert named.failed
    assert "bool" in named.detail
