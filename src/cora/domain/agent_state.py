"""The state one turn of the agent accumulates."""

import operator
from typing import Annotated, Any, TypedDict

from cora.domain.citations import Citation
from cora.domain.trace import TraceStep
from cora.ports.chat_model import Message


class AgentState(TypedDict, total=False):
    """One conversation's state, as it stands part-way through a turn.

    Annotated keys accumulate — `messages` is the thread's transcript and `citations`
    its registry, both spanning every turn — while the rest are set once per turn.

    `turn_start` and `trace_start` mark where this turn begins in the transcript and in
    the trace, so what a turn has spent is read off them rather than counted, and a turn
    picked up after a pause still reports the steps it took before it stopped.

    `pin` is the scope the conversation was fixed to, set once and answered under by
    every later turn. `pinning` is what *this* turn asked to pin, a key apart because a
    turn refused on the way in must fix nothing.
    """

    question: str
    messages: Annotated[list[Message], operator.add]
    trace: Annotated[list[TraceStep], operator.add]
    citations: Annotated[list[Citation], operator.add]
    turn_start: int
    trace_start: int
    scopes: list[str]
    candidates: list[str]
    pin: str
    pinning: str
    filled: dict[str, dict[str, Any]]
    kept: dict[str, dict[str, str]]
    brief: str
    answer: str
