"""What taking part in a turn means at each point one can be taken part in.

A plugin subscribes by name, and the names are `cora.ports.host`'s: they are what a
plugin writes. What a handler's return *means* is here — an event either refuses its
value or amends it, and that is the whole of the difference. A new point in the turn
is an entry in `EVENTS`; a new meaning is a class beside the two below. Neither is a
branch anyone has to find.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cora.domain.errors import CoreError, InputRejectedError
from cora.domain.trace import HandlerRan, TraceStep
from cora.engine.scoping import running_in
from cora.ports.host import (
    BRIEFING,
    CALLING,
    RETURNING,
    SCREENING,
    Registration,
    Subscription,
)
from cora.ports.plugin import ToolRefusal, ToolResult

log = logging.getLogger(__name__)

UNSCREENED = "Your question could not be checked, so it was not answered."
"""What the user reads when a screening handler broke rather than refused. It says what
happened and stops: what the handler was holding could be anything, so nothing of it is
quoted — not to the user, and not to the model."""
UNCHECKED = "a plugin could not check this call"
"""What the model is told when a handler on a call broke. The call does not run: a check
that failed is not a check that passed."""


@dataclass(frozen=True)
class Refusing:
    """An event whose handlers may refuse its value, and may not change it.

    Answering with anything is refusing, and a sentence is the reason. Answering with
    something that is not one refuses too, on cora's own wording: fail closed, and never
    on a plugin's repr. A handler that raises refuses as well — a broken rule must not
    admit an input — and only the kind of what it raised is passed on, because the
    message could be carrying whatever the handler held.
    """

    refusal: type[Exception]
    reason: str
    refused: str
    broke: str

    def raised(self, reason: str) -> Exception:
        """The refusal this event ends with, as the exception it is raised as."""
        return self.refusal(reason)


@dataclass(frozen=True)
class Amending:
    """An event whose handlers may change its value, each handed what the last returned.

    A handler answering with nothing leaves the value as it was, so watching needs no
    kind of its own: an observer is an amender that amends nothing. A handler that
    raises is dropped and the turn carries on — a lost amendment is not a lost turn.

    `holds` is what the value is, and an answer that is not one is dropped like a raise:
    failing open means a plugin cannot cost the turn, and a brief that came back as a
    dictionary would cost it just as surely as an exception.
    """

    amended: str
    broke: str
    holds: type


Kind = Refusing | Amending
"""What an event does with what its handlers answer."""

EVENTS: Mapping[str, Kind] = {
    SCREENING: Refusing(
        refusal=InputRejectedError,
        reason=UNSCREENED,
        refused="refused the question",
        broke="could not screen the question",
    ),
    BRIEFING: Amending(
        amended="amended the brief",
        broke="could not amend the brief",
        holds=str,
    ),
    CALLING: Refusing(
        refusal=ToolRefusal,
        reason=UNCHECKED,
        refused="refused a tool call",
        broke="could not check a tool call",
    ),
    RETURNING: Amending(
        amended="changed a tool result",
        broke="could not change a tool result",
        holds=ToolResult,
    ),
}
"""Every point in a turn a plugin can take part in, and what it does there."""


def dispatch(
    event: str,
    value: Any,
    handlers: tuple[Registration, ...],
    trace: list[TraceStep],
    scopes: frozenset[str] = frozenset(),
) -> Any:
    """Run one event's handlers, in order, and answer with the value to carry on with.

    Amendments chain: each handler is handed what the one before it returned, so the
    value that comes back is what all of them made of it. On a refusing event nothing
    chains — the value is what was handed in, or the event's exception is raised.

    This and `ToolRuntime.execute` are the two places a plugin's own code runs, so both
    bind the turn's field around it: a handler that reads the documents reads the field
    the turn is in, and material from another one never reaches the brief.

    Args:
        handlers: What is subscribed to this event, already narrowed to the turn's
            scopes and in the order they registered.
        trace: Where a step is appended per handler that did something, in order. Kept
            by the caller, so a refusal leaves behind what it interrupted.
        scopes: What the turn is running under. Empty where it is not settled yet —
            screening runs before routing, so a screen reads the default field.

    Raises:
        InputRejectedError: A handler refused the question, or broke while screening it.
        ToolRefusal: A handler refused the call, or broke while checking it. The turn
            answers anyway: the model is told, and no round is spent.
    """
    with running_in(scopes):
        return _ran(event, value, handlers, trace)


def _ran(
    event: str,
    value: Any,
    handlers: tuple[Registration, ...],
    trace: list[TraceStep],
) -> Any:
    kind = EVENTS[event]
    for entry in handlers:
        subscription: Subscription = entry.value
        try:
            answered = subscription.handle(value)
        except Exception as broke:
            # Logged as well as traced: a question refused on the way in ends the turn,
            # and the operator is the only reader left once the trace goes with it. The
            # kind of what was raised and nothing else, as everywhere else.
            log.warning(
                "%s raised %s on '%s'", entry.module, type(broke).__name__, event
            )
            _took(trace, entry, event, kind.broke, type(broke).__name__, failed=True)
            if isinstance(kind, Refusing):
                raise _ending(kind, kind.reason, trace) from broke
            continue
        if answered is None:
            continue
        if isinstance(kind, Refusing):
            if not isinstance(answered, str):
                _took(
                    trace,
                    entry,
                    event,
                    kind.broke,
                    type(answered).__name__,
                    failed=True,
                )
                raise _ending(kind, kind.reason, trace)
            _took(trace, entry, event, kind.refused, answered)
            raise _ending(kind, answered, trace)
        if not isinstance(answered, kind.holds):
            _took(trace, entry, event, kind.broke, type(answered).__name__, failed=True)
            continue
        _took(trace, entry, event, kind.amended, "")
        value = answered
    return value


def _took(
    trace: list[TraceStep],
    entry: Registration,
    event: str,
    outcome: str,
    detail: str,
    failed: bool = False,
) -> None:
    trace.append(
        HandlerRan(
            plugin=entry.module,
            event=event,
            outcome=outcome,
            detail=detail,
            failed=failed,
        )
    )


def _ending(kind: Refusing, reason: str, trace: list[TraceStep]) -> Exception:
    """The refusal, carrying the steps the turn took on its way to being refused.

    A turn refused on the way in never reaches a state, so the trace travels on the
    exception or nowhere: it is what says which plugin refused, and the user is owed it.
    """
    raised = kind.raised(reason)
    if isinstance(raised, CoreError):
        raised.trace = tuple(trace)
    return raised
