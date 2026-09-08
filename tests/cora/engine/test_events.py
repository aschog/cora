"""What a handler's return means at each point in a turn."""

import pytest

from cora.domain.errors import InputRejectedError
from cora.domain.trace import TraceStep
from cora.engine.events import EVENTS, dispatch
from cora.ports.host import (
    ANSWERING,
    BRIEFING,
    CALLING,
    HANDLER,
    RETURNING,
    SCREENING,
    Handler,
    Registration,
    Subscription,
)

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


def test_every_point_a_plugin_may_subscribe_to_is_in_the_table() -> None:
    assert set(EVENTS) == {SCREENING, BRIEFING, CALLING, RETURNING, ANSWERING}
