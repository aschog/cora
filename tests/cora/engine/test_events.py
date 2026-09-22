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
    TAKING,
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


def _takes(text: str) -> Handler:
    def take(question: str) -> str:
        return text

    return take


def test_the_first_taker_answers_and_the_rest_never_run() -> None:
    trace: list[TraceStep] = []
    offered: list[str] = []

    def second(question: str) -> str:
        offered.append(question)
        return "second"

    taken = dispatch(
        TAKING,
        "q",
        (
            _subscribed(FIRST, TAKING, _takes("first")),
            _subscribed(SECOND, TAKING, second),
        ),
        trace,
    )

    assert taken == "first"
    assert offered == []
    assert [step.summary for step in trace] == [f"{FIRST} took the question"]


def test_a_question_nobody_took_comes_back_as_nothing() -> None:
    trace: list[TraceStep] = []

    taken = dispatch(
        TAKING, "q", (_subscribed(FIRST, TAKING, lambda question: None),), trace
    )

    assert taken is None
    assert trace == []


def test_a_taker_answering_with_anything_but_text_is_dropped_for_the_next() -> None:
    trace: list[TraceStep] = []

    taken = dispatch(
        TAKING,
        "q",
        (
            _subscribed(FIRST, TAKING, lambda question: {"answer": question}),
            _subscribed(SECOND, TAKING, _takes("second")),
        ),
        trace,
    )

    assert taken == "second"
    broke, took = trace
    assert broke.failed and "dict" in broke.detail
    assert took.summary == f"{SECOND} took the question"


def test_a_taker_that_raises_is_dropped_and_the_next_one_runs() -> None:
    trace: list[TraceStep] = []

    taken = dispatch(
        TAKING,
        "q",
        (
            _subscribed(FIRST, TAKING, _breaks),
            _subscribed(SECOND, TAKING, _takes("second")),
        ),
        trace,
    )

    assert taken == "second"
    broke, _ = trace
    assert broke.failed
    assert "RuntimeError" in broke.detail
    assert "hunter2" not in broke.detail


def test_blank_text_takes_nothing() -> None:
    trace: list[TraceStep] = []

    taken = dispatch(TAKING, "q", (_subscribed(FIRST, TAKING, _takes("  \n")),), trace)

    assert taken is None
    assert trace == []


def test_every_point_a_plugin_may_subscribe_to_is_in_the_table() -> None:
    assert set(EVENTS) == {
        SCREENING,
        BRIEFING,
        TAKING,
        CALLING,
        RETURNING,
        ANSWERING,
    }
