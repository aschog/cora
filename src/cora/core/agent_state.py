import operator
from typing import Annotated, TypedDict

from cora.core.citations import Source
from cora.core.ports.chat_model import Message
from cora.core.trace import TraceStep
from cora.core.turn import Turn


class AgentState(TypedDict, total=False):
    """One run's state. Annotated keys accumulate across steps; the rest are set
    once. A step returns only the keys it contributes."""

    question: str
    history: tuple[Turn, ...]
    messages: Annotated[list[Message], operator.add]
    trace: Annotated[list[TraceStep], operator.add]
    sources: Annotated[list[Source], operator.add]
    rounds: Annotated[int, operator.add]
    answer: str
