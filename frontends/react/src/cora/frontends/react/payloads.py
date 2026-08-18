"""Domain objects as the JSON the page reads.

One module because the page and the API have to agree on one shape, and the shape is
not the domain's business: a `TraceStep` is a class hierarchy the engine grows, and the
panel that draws it wants three keys whatever kind arrived.
"""

from typing import Any

from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.trace import ToolUse, TraceStep
from cora.engine.plugin_set import RESERVED_TOOL_NAMES
from cora.ports.memory import Fact


def citation(citation: Citation) -> dict[str, Any]:
    return {
        "number": citation.number,
        "document": citation.document,
        "start": citation.start,
        "end": citation.end,
        "upload": citation.upload,
    }


def step(step: TraceStep) -> dict[str, Any]:
    """Four keys whatever kind of step arrived, so the panel draws one thing. A kind the
    engine grows next carries the first three off the base class and claims no origin,
    rather than needing this module to have heard of it."""
    return {
        "summary": step.summary,
        "detail": step.detail,
        "failed": step.failed,
        "origin": _origin(step),
    }


def _origin(step: TraceStep) -> str:
    """What cora offers before a plugin is loaded is the engine's own list — the one a
    plugin's tool names are refused against — so a built-in added there is a built-in
    here too, rather than a name this module also had to be told."""
    if not isinstance(step, ToolUse):
        return ""
    return "core retrieval" if step.name in RESERVED_TOOL_NAMES else "plugin tool"


def result(result: ChatResult) -> dict[str, Any]:
    return {
        "answer": result.answer,
        "citations": [citation(each) for each in result.citations],
        "trace": [step(each) for each in result.trace],
    }


def turn(turn: Turn) -> dict[str, Any]:
    return {"question": turn.question, "result": result(turn.result)}


def fact(fact: Fact) -> dict[str, Any]:
    return {"key": fact.key, "text": fact.text}


def session(session: Session) -> dict[str, Any]:
    return {"thread_id": session.thread_id, "opened_with": session.opened_with}
