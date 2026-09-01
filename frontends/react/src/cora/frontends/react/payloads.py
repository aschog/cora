"""Domain objects as the JSON the page reads.

One module because the page and the API have to agree on one shape, and the shape is
not the domain's business: a `TraceStep` is a class hierarchy the engine grows, and the
panel that draws it wants three keys whatever kind arrived.
"""

from typing import Any

from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.decision import Decision, Option, Pending
from cora.domain.trace import ToolUse, TraceStep
from cora.engine.plugin_set import RESERVED_TOOL_NAMES
from cora.ports.host import Listed
from cora.ports.memory import Fact


def citation(citation: Citation) -> dict[str, Any]:
    return {
        "number": citation.number,
        "document": citation.document,
        "start": citation.start,
        "end": citation.end,
        "upload": citation.upload,
        "scope": citation.scope,
    }


def step(taken: TraceStep) -> dict[str, Any]:
    """Five keys whatever kind of step arrived, so the panel draws one thing. A kind the
    engine grows next carries the first three off the base class and claims no origin,
    rather than needing this module to have heard of it. `steps` is what the step did
    inside itself — empty for all but a tool that ran work of its own."""
    return {
        "summary": taken.summary,
        "detail": taken.detail,
        "failed": taken.failed,
        "origin": _origin(taken),
        "steps": [step(child) for child in taken.steps],
    }


def _origin(step: TraceStep) -> str:
    """Whose tool the step reached for, which is the whole claim the plugin architecture
    makes. What cora offers before a plugin is loaded is the engine's own list — the one
    a plugin's tool names are refused against — so a built-in added there is a built-in
    here too, rather than a name this module also had to be told. What the tool *did* is
    the step's own summary: the list holds a memory write as well as a search, and one
    label over both can only be the thing they have in common."""
    if not isinstance(step, ToolUse):
        return ""
    return "core tool" if step.name in RESERVED_TOOL_NAMES else "plugin tool"


def result(result: ChatResult) -> dict[str, Any]:
    return {
        "answer": result.answer,
        "citations": [citation(each) for each in result.citations],
        "trace": [step(each) for each in result.trace],
        "scopes": list(result.scopes),
    }


def turn(turn: Turn) -> dict[str, Any]:
    return {"question": turn.question, "result": result(turn.result)}


def option(option: Option) -> dict[str, Any]:
    return {"label": option.label, "note": option.note}


def decision(decision: Decision) -> dict[str, Any]:
    return {
        "question": decision.question,
        "options": [option(each) for each in decision.options],
        "decline": decision.decline,
    }


def pending(pending: Pending) -> dict[str, Any]:
    """A turn parked on a question, with the question that opened it: a paused turn is
    in no store, so the page has nothing else to draw the card under."""
    return {"asked": pending.asked, "decision": decision(pending.decision)}


def fact(fact: Fact) -> dict[str, Any]:
    return {"key": fact.key, "text": fact.text}


def session(session: Session) -> dict[str, Any]:
    return {"thread_id": session.thread_id, "opened_with": session.opened_with}


def plugin(listed: Listed) -> dict[str, Any]:
    """One loaded plugin as the header menu draws it.

    The contributions arrive as one list of the same three keys whatever kind they are,
    so the menu renders a kind it has never heard of rather than dropping it.
    """
    return {
        "name": listed.name,
        "source": listed.source,
        "scopes": list(listed.scopes),
        "contributions": [
            {
                "kind": each.kind,
                "name": each.name,
                "scope": each.scope,
            }
            for each in listed.contributions
        ],
    }
