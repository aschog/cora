"""What a tool did inside its call, collected while the call runs.

A plugin's tool may run a loop of its own, and what that loop does belongs under the
call rather than beside it. The collector is a context variable so a tool reaches it
without being handed it, and so two turns answering at once never share one.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from cora.domain.trace import TraceStep


@dataclass
class Inside:
    """What happened while one call ran: the steps it took, and what it read.

    `untrusted` is set by whoever read the user's documents into the call, at whatever
    depth, so the call's own result is labelled for what went into it rather than for
    what it happens to look like coming out.
    """

    steps: list[TraceStep] = field(default_factory=list)
    untrusted: bool = False


_inside: ContextVar[Inside | None] = ContextVar("_inside", default=None)


@contextmanager
def collecting() -> Iterator[Inside]:
    """Collect what happens while this block runs, for whoever ran it.

    What the block read carries outward when it ends: a loop three calls deep that read
    a document has read it into every call above it, and each of them says so.
    """
    taken = Inside()
    token = _inside.set(taken)
    try:
        yield taken
    finally:
        _inside.reset(token)
        outer = _inside.get()
        if taken.untrusted and outer is not None:
            outer.untrusted = True


def took(step: TraceStep) -> None:
    """Report a step to the call it was taken inside, if there is one.

    Outside a call there is nothing to report to, and a step taken there is dropped:
    a plugin running a loop of its own before a turn is not part of any turn's trace.
    """
    taken = _inside.get()
    if taken is not None:
        taken.steps.append(step)


def read_untrusted() -> None:
    """Say that the user's documents were read into the call this is running inside.

    Whatever the call answers with was built out of material cora does not vouch for,
    so the answer is labelled on the way back however far it is from the passage.
    Outside a call there is nothing to tell, and nothing is recorded.
    """
    taken = _inside.get()
    if taken is not None:
        taken.untrusted = True
