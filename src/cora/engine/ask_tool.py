from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from cora.domain.decision import Decision, Option
from cora.ports.plugin import Tool, ToolRefusal

ASK_TOOL_NAME = "ask_user"
NOT_A_DECISION = "invalid arguments: {reason}"
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
    """The call as a decision, or a refusal written for the model that made it. The
    schema is the tool's own, so a malformed ask is refused the way a malformed call to
    any other tool is — the round hears about it and carries on."""
    try:
        Draft202012Validator(ASK_SCHEMA).validate(arguments)
    except ValidationError as invalid:
        raise ToolRefusal(NOT_A_DECISION.format(reason=invalid.message)) from invalid
    return Decision(
        question=arguments["question"],
        options=tuple(
            Option(label=offered["label"], note=offered.get("note", ""))
            for offered in arguments["options"]
        ),
        decline=arguments.get("decline", ""),
    )


def _asked_already(**_: Any) -> str:
    """The one tool whose work is not its own. The router sends the ask that will stop
    the run to the step that can stop it, ahead of the round's tools — so the dispatcher
    reaches this only for an ask that will not: a second one in the same round, or one
    raised after the reader has already been stopped. Either way what the round needs to
    hear is why, not that it found an unreachable branch."""
    raise ToolRefusal(ASKED_ALREADY)


def ask_tool() -> Tool:
    return Tool(
        name=ASK_TOOL_NAME,
        description=ASK_TOOL_DESCRIPTION,
        parameter_schema=ASK_SCHEMA,
        run=_asked_already,
    )
