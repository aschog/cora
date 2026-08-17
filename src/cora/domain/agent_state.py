import operator
from typing import Annotated, TypedDict

from cora.domain.citations import Source
from cora.domain.trace import TraceStep
from cora.ports.chat_model import Message


class AgentState(TypedDict, total=False):
    """One conversation's state. Annotated keys accumulate — `messages` is the
    thread's append-only transcript and `sources` its citation registry, both
    spanning every turn — while the rest are set once per turn. A step returns only
    the keys it contributes.

    `turn_start` is where the current turn begins in the transcript: everything a
    turn needs to know about *itself* rather than the conversation — how many model
    calls it has spent — is read from there, so no counter has to be reset and none
    can carry over."""

    question: str
    messages: Annotated[list[Message], operator.add]
    trace: Annotated[list[TraceStep], operator.add]
    sources: Annotated[list[Source], operator.add]
    turn_start: int
    brief: str
    answer: str
