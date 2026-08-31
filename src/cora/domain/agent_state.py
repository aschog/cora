"""The state one turn of the agent accumulates."""

import operator
from typing import Annotated, TypedDict

from cora.domain.citations import Citation
from cora.domain.trace import TraceStep
from cora.ports.chat_model import Message


class AgentState(TypedDict, total=False):
    """One conversation's state, as it stands part-way through a turn.

    Annotated keys accumulate — `messages` is the thread's append-only transcript and
    `citations` its citation registry, both spanning every turn — while the rest are set
    once per turn. A step returns only the keys it contributes.

    `turn_start` is where the current turn begins in the transcript: everything a
    turn needs to know about *itself* rather than the conversation — how many model
    calls it has spent — is read from there, so no counter has to be reset and none
    can carry over. `trace_start` is the same mark in the trace, and it is what lets a
    turn picked up after a pause still report every step it took, including the ones
    taken before it stopped.

    `scopes` is what the turn is running under: which of the registrations the plugins
    made apply to it. Settled by the routing step and checkpointed with the rest, so a
    turn resumed after a pause is the same turn it was.

    `pin` is the scope the *conversation* was fixed to, which is the one key here that
    is not a turn's. It is set once, by the user and by nobody else, and every later
    turn on the thread is answered under it — so a reopened thread reopens in its field
    rather than being read afresh.
    """

    question: str
    messages: Annotated[list[Message], operator.add]
    trace: Annotated[list[TraceStep], operator.add]
    citations: Annotated[list[Citation], operator.add]
    turn_start: int
    trace_start: int
    scopes: list[str]
    pin: str
    brief: str
    answer: str
