import operator
from typing import Annotated, TypedDict

from cora.core.domain.citations import Source
from cora.core.domain.trace import TraceStep
from cora.core.domain.turn import Turn
from cora.core.ports.chat_model import Message


class AgentState(TypedDict, total=False):
    """One run's state. Annotated keys accumulate across steps; the rest are set
    once. A step returns only the keys it contributes."""

    question: str
    history: tuple[Turn, ...]
    messages: Annotated[list[Message], operator.add]
    trace: Annotated[list[TraceStep], operator.add]
    sources: Annotated[list[Source], operator.add]
    rounds: Annotated[int, operator.add]
    answer_in_hand: str
    answer: str
