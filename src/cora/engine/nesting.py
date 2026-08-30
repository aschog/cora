"""What a tool did inside its call, collected while the call runs.

A plugin's tool may run a loop of its own, and what that loop does belongs under the
call rather than beside it. The collector is a context variable so a tool reaches it
without being handed it, and so two turns answering at once never share one.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from cora.domain.trace import TraceStep

_inside: ContextVar[list[TraceStep] | None] = ContextVar("_inside", default=None)


@contextmanager
def collecting() -> Iterator[list[TraceStep]]:
    """Collect the steps taken while this block runs, for whoever ran it."""
    taken: list[TraceStep] = []
    token = _inside.set(taken)
    try:
        yield taken
    finally:
        _inside.reset(token)


def took(step: TraceStep) -> None:
    """Report a step to the call it was taken inside, if there is one.

    Outside a call there is nothing to report to, and a step taken there is dropped:
    a plugin running a loop of its own before a turn is not part of any turn's trace.
    """
    taken = _inside.get()
    if taken is not None:
        taken.append(step)
