"""The two tools that stop a turn: which of two facts was meant, and what cora lacks."""

from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from cora.domain.card import ActionOffered, Card, fields_of
from cora.domain.decision import Decision, Option
from cora.ports.plugin import Tool, ToolRefusal

ASK_TOOL_NAME = "ask_user"
NOT_READABLE = "invalid arguments: {reason}"
ASKED_ALREADY = (
    "You have already asked this turn. Answer with what you were given rather than "
    "asking a second time."
)
ASK_TOOL_DESCRIPTION = (
    "Ask the user to settle one thing you cannot settle yourself, then wait. Use it "
    "when what you already know about them holds the same fact at two or more "
    "different values, nothing says which is current, and the answer depends on it. "
    "Offer the values you actually found, one option each, and say in the note where "
    "each came from. Never ask to be polite, never ask what you could look up, and "
    "never ask a question you could answer and let them correct."
)
ASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "The one thing to settle, asked in a single sentence.",
        },
        "options": {
            "type": "array",
            "description": "The ways you found, in the order you would rank them.",
            "minItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "The value itself — '75 kg', not a sentence.",
                    },
                    "note": {
                        "type": "string",
                        "description": (
                            "Where this one came from, so two can be told apart — "
                            "'coach notes, February'."
                        ),
                    },
                },
                "required": ["label"],
            },
        },
        "decline": {
            "type": "string",
            "description": "What choosing none of them says, in the user's voice.",
        },
    },
    "required": ["question", "options"],
}


def decision_from(arguments: dict[str, Any]) -> Decision:
    """The call as a decision, or a refusal written for the model that made it.

    The schema is the tool's own, so a malformed ask is refused the way a malformed call
    to any other tool is — the round hears about it and carries on.

    Raises:
        ToolRefusal: The arguments are not a decision. The message quotes what was
            wrong, so the model can ask properly instead.
    """
    try:
        Draft202012Validator(ASK_SCHEMA).validate(arguments)
    except ValidationError as invalid:
        raise ToolRefusal(NOT_READABLE.format(reason=invalid.message)) from invalid
    return Decision(
        question=arguments["question"],
        options=tuple(
            Option(label=offered["label"], note=offered.get("note", ""))
            for offered in arguments["options"]
        ),
        decline=arguments.get("decline", ""),
    )


ASK_FOR_TOOL_NAME = "ask_user_for"
ASK_FOR_TOOL_DESCRIPTION = (
    "Ask the user for values you do not have and cannot look up, then wait. They are "
    "put one form of the fields you name, and what they write comes back as this "
    "call's result. Use it rather than asking for them in your answer: an answer that "
    "asks is a turn spent, and a form is not. Name the values the answer turns on and "
    "no others, never one you could look up, and never one they have already given."
)
DRAWN = ("string", "integer", "number", "boolean")
"""The kinds of value a field may ask for. Not every JSON Schema type: an object or an
array is a shape the page has no control for, and a card the reader cannot answer is
worse than an ask that was refused."""
ASK_FOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "What you need and what for, in a single sentence.",
        },
        "fields": {
            "type": "array",
            "description": "The values you need, in the order they are best filled in.",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "What to call it — 'origin', not a sentence.",
                    },
                    "description": {
                        "type": "string",
                        "description": "What to write in it, as the reader's label.",
                    },
                    "type": {
                        "type": "string",
                        "enum": list(DRAWN),
                        "description": "The kind of value. A string unless you say so.",
                    },
                    "format": {
                        "type": "string",
                        "description": (
                            "'date' where the value is a day, so the reader is given a "
                            "date control rather than a box to mistype one into."
                        ),
                    },
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "The values to pick between, where there is a fixed set of "
                            "them. Left out, the reader writes their own."
                        ),
                    },
                    "required": {
                        "type": "boolean",
                        "description": (
                            "Whether the answer needs this one. The form cannot be "
                            "submitted without it, so mark only what it turns on."
                        ),
                    },
                },
                "required": ["name", "description"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["prompt", "fields"],
}

SEND = "Send"
NOT_NOW = "Not now"
SENT = "You filled it in."
NOT_SENT = "You did not fill it in."
ASKED_TWICE = "two fields are called '{name}', so one of them could not be asked for"


def card_from(arguments: dict[str, Any]) -> Card:
    """The call as the card the reader is put, or a refusal written for the model.

    The fields the model named become a JSON Schema object, and the card is built from
    that the way a tool's card is built from the schema it declared — so a value asked
    for here is drawn by the control that value's schema already earns.

    Raises:
        ToolRefusal: The ask is not readable as a form. The message quotes what was
            wrong, so the model can ask properly rather than spend the turn's question
            on a card nobody could answer.
    """
    try:
        Draft202012Validator(ASK_FOR_SCHEMA).validate(arguments)
    except ValidationError as invalid:
        raise ToolRefusal(NOT_READABLE.format(reason=invalid.message)) from invalid
    wanted = arguments["fields"]
    named: dict[str, Any] = {}
    for field in wanted:
        if field["name"] in named:
            raise ToolRefusal(ASKED_TWICE.format(name=field["name"]))
        named[field["name"]] = _property(field)
    return Card(
        prompt=arguments["prompt"],
        fields=fields_of(
            {
                "type": "object",
                "properties": named,
                "required": [
                    field["name"] for field in wanted if field.get("required")
                ],
            }
        ),
        actions=(
            ActionOffered(label=SEND, answer=SEND, needs_valid=True, settled=SENT),
            ActionOffered(label=NOT_NOW, answer=None, settled=NOT_SENT),
        ),
    )


def _property(field: dict[str, Any]) -> dict[str, Any]:
    """One field the model named, as the schema of the value it asks for."""
    return {
        "type": field.get("type", "string"),
        "description": field["description"],
        **({"format": field["format"]} if field.get("format") else {}),
        **({"enum": field["choices"]} if field.get("choices") else {}),
    }


def _asked_already(**_: Any) -> str:
    """The one tool whose work is not its own.

    The router sends the ask that will stop the run to the step that can stop it, ahead
    of the round's tools — so the dispatcher reaches this only for an ask that will not:
    a second one in the same round, or one raised after the reader has already been
    stopped. Either way what the round needs to hear is why, not that it found an
    unreachable branch.

    Raises:
        ToolRefusal: Always. The turn has had its question.
    """
    raise ToolRefusal(ASKED_ALREADY)


def ask_tool() -> Tool:
    """The `ask_user` tool as the model is offered it.

    Running it is a refusal by design: what a real ask does is stop the run, which is
    `AskStep`'s to do and no tool's.
    """
    return Tool(
        name=ASK_TOOL_NAME,
        description=ASK_TOOL_DESCRIPTION,
        parameter_schema=ASK_SCHEMA,
        run=_asked_already,
    )


def ask_for_tool() -> Tool:
    """The `ask_user_for` tool as the model is offered it.

    Running it is a refusal for the reason `ask_tool`'s is: what a real ask does is stop
    the run, which is `AskStep`'s to do and no tool's.
    """
    return Tool(
        name=ASK_FOR_TOOL_NAME,
        description=ASK_FOR_TOOL_DESCRIPTION,
        parameter_schema=ASK_FOR_SCHEMA,
        run=_asked_already,
    )
