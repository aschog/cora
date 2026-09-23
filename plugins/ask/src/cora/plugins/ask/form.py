from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from cora.domain.card import ActionOffered, Card, fields_of
from cora.ports.plugin import ToolRefusal

ASK_FOR_TOOL_NAME = "ask_user_for"
NOT_READABLE = "invalid arguments: {reason}"
FORM_DESCRIPTION = (
    "Ask the user for two or more values you do not have and cannot look up, then "
    "wait. They are put one form of the fields you name, and what they write comes "
    "back as this call's result. Use it rather than asking for them in your answer: an "
    "answer that asks for four things is a turn spent, and a form is not. Where one "
    "value is all you are missing, ask for that one in your answer instead — a form of "
    "one box is a stop the sentence already made. Name the values the answer turns on "
    "and no others, never one you could look up, and never one they have already given."
)
DRAWN = ("string", "integer", "number", "boolean")
MOST_FIELDS = 12
ASK_FOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "What you need and what for, in a single sentence.",
            "minLength": 1,
        },
        "fields": {
            "type": "array",
            "description": (
                "The values you need, in the order they are best filled in. Two or "
                "more: one value is asked for in your answer, not on a card."
            ),
            "minItems": 2,
            "maxItems": MOST_FIELDS,
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

ONE_VALUE = (
    "'{name}' is one value, and a card is how two or more of them are asked for. Ask "
    "for it in your answer instead, in a sentence — the user replies in prose, and the "
    "next turn has it."
)
SEND = "Send"
NOT_NOW = "Not now"
SENT = "You filled it in."
NOT_SENT = "You did not fill it in."
ASKED_TWICE = "two fields are called '{name}', so one of them could not be asked for"
WRITTEN_IN = "The user filled the form in — {values}. Those are their own words."
NOTHING_WRITTEN = (
    "The user filled in nothing. Carry on without those values, say plainly what you "
    "still need, and do not ask again."
)
OWN = frozenset({"prompt", "fields"})


def card_of_form(arguments: dict[str, Any]) -> Card:
    """The call as the card the reader is put, or a refusal written for the model.

    The fields the model named become a JSON Schema object, and the card is built from
    that the way a tool's card is built from the schema it declared — so a value asked
    for here is drawn by the control that value's schema already earns.

    Raises:
        ToolRefusal: The ask is not readable as a form. The message quotes what was
            wrong, so the model can ask properly rather than spend the turn's question
            on a card nobody could answer.
    """
    _refuse_one_field(arguments.get("fields"))
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


def fill(**arguments: Any) -> str:
    """What the reader wrote, as the model reads it, or that they wrote nothing."""
    written = {name: value for name, value in arguments.items() if name not in OWN}
    if not written:
        return NOTHING_WRITTEN
    return WRITTEN_IN.format(values=_values(written))


def _refuse_one_field(fields: Any) -> None:
    if not isinstance(fields, list) or len(fields) != 1:
        return
    [named] = fields
    asked = named.get("name") if isinstance(named, Mapping) else None
    raise ToolRefusal(ONE_VALUE.format(name=asked or "the value"))


def _property(field: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": field.get("type", "string"),
        "description": field["description"],
        **({"format": field["format"]} if field.get("format") else {}),
        **({"enum": field["choices"]} if field.get("choices") else {}),
    }


def _values(written: dict[str, Any]) -> str:
    return ", ".join(f"{name}={value!r}" for name, value in sorted(written.items()))
