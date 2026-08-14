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
    calls it has spent, whether it has used a tool — is read from there, so no
    counter has to be reset and none can carry over.

    `reconsidered` says the grounding gate has had its turn; `answer_in_hand` says
    what it is holding. Two keys, because an answer can be empty and the gate still
    have run — conflating them would send an empty answer round the gate forever."""

    question: str
    messages: Annotated[list[Message], operator.add]
    trace: Annotated[list[TraceStep], operator.add]
    sources: Annotated[list[Source], operator.add]
    turn_start: int
    brief: str
    reconsidered: bool
    answer_in_hand: str
    answer: str
