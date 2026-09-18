"""Domain objects as the JSON the page reads.

One module because the page and the API have to agree on one shape, and the shape is
not the domain's business: a `TraceStep` is a class hierarchy the engine grows, and the
panel that draws it wants three keys whatever kind arrived.
"""

from typing import Any

from cora.domain.card import ActionOffered, Card, FieldAsked
from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.decision import Pending
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


def asked(field: FieldAsked) -> dict[str, Any]:
    """One value on a card, with the schema the page draws its control from."""
    return {
        "name": field.name,
        "schema": field.schema,
        "value": field.value,
        "editable": field.editable,
        "required": field.required,
    }


def action(action: ActionOffered) -> dict[str, Any]:
    """One way off a card. `answer` is what travels back when it is taken, and `null`
    is the way out — a decline, or none of them."""
    return {
        "label": action.label,
        "answer": action.answer,
        "note": action.note,
        "needs_valid": action.needs_valid,
        "settled": action.settled,
    }


def card(card: Card) -> dict[str, Any]:
    """What a stopped turn puts to the reader, whichever way it stopped. One shape, so
    the page draws it from the payload rather than from what stopped the turn."""
    return {
        "prompt": card.prompt,
        "fields": [asked(each) for each in card.fields],
        "actions": [action(each) for each in card.actions],
    }


def pending(pending: Pending) -> dict[str, Any]:
    """A turn parked on something to settle, with the question that opened it: a paused
    turn is in no store, so the page has nothing else to draw the card under."""
    return {"asked": pending.asked, "card": card(pending.card)}


def fact(fact: Fact) -> dict[str, Any]:
    return {"key": fact.key, "text": fact.text}


def session(session: Session, pin: str | None) -> dict[str, Any]:
    """One conversation as the list draws it, and the field it is fixed to.

    The pin rather than the fields its turns were answered in: the first is a decision
    the reader made about the conversation, the second a reading of one question. A
    listing is where they are told apart, so it is the decision that is sent.
    """
    return {
        "thread_id": session.thread_id,
        "opened_with": session.opened_with,
        "pin": pin,
    }


def plugin(listed: Listed, deletable: bool, going: tuple[str, ...]) -> dict[str, Any]:
    """One loaded plugin as the header menu draws it.

    The contributions arrive as one list of the same four keys whatever kind they are,
    so the menu renders a kind it has never heard of rather than dropping it. `note` is
    whatever else a registration says about itself — a tool with an effect says so —
    and the menu shows it without having to know what it means.

    `deletable` is cora's answer rather than the page's reading of the source: whether
    a plugin can be deleted is a fact about where this deployment found it. `going` is
    the fields deleting it would take, which is not every field it registered — one
    something else also brings stays, and the question the reader answers says so.
    """
    return {
        "name": listed.name,
        "source": listed.source,
        "scopes": list(listed.scopes),
        "deletable": deletable,
        "going": list(going),
        "contributions": [
            {
                "kind": each.kind,
                "name": each.name,
                "scope": each.scope,
                "note": each.note,
            }
            for each in listed.contributions
        ],
    }
