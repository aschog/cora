from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from cora.domain.card import ActionOffered, Card
from cora.ports.host import State
from cora.ports.plugin import ToolRefusal

ASK_TOOL_NAME = "ask_user"
CHOSEN = "chosen"
# What the way out answers with. A card that lands its action has to hand the tool
# something for a decline too, or the gate reads the decline as a card left unconfirmed.
# Its own word rather than an option's place, because it is not one of the options.
NONE_TAKEN = "none"
NO_OPTION = "None of them"
DECLINED = "You chose none of them."
NOT_READABLE = "invalid arguments: {reason}"
FORKED = "forked"
ASKED_ALREADY = (
    "You have already asked this in this conversation. Answer with what you were "
    "given rather than asking a second time."
)
NOTHING_CHOSEN = (
    "The user chose none of the options. Carry on without one, say what you could not "
    "settle, and do not ask again."
)
FORK_DESCRIPTION = (
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


def card_of_fork(arguments: dict[str, Any], state: State | None = None) -> Card:
    """The call as the card the reader is put: one action per option, and a way out.

    Args:
        state: What this plugin kept for the conversation, where the fork already put
            is remembered. Given none, nothing is remembered and every fork stands.

    Raises:
        ToolRefusal: The arguments are not a fork, or this fork was put already in this
            conversation. The message says which, so the model can go on properly.
    """
    try:
        Draft202012Validator(ASK_SCHEMA).validate(arguments)
    except ValidationError as invalid:
        raise ToolRefusal(NOT_READABLE.format(reason=invalid.message)) from invalid
    if state is not None and state.read(FORKED) == arguments["question"]:
        raise ToolRefusal(ASKED_ALREADY)
    return Card(
        prompt=arguments["question"],
        actions=(
            *(
                ActionOffered(
                    label=offered["label"],
                    # Where it stands rather than what it says: two values the model
                    # labels alike are still two options, and a label that happens to
                    # read like the way out is still a choice of that value.
                    answer=str(at),
                    note=offered.get("note", ""),
                )
                for at, offered in enumerate(arguments["options"])
            ),
            ActionOffered(
                label=arguments.get("decline") or NO_OPTION,
                answer=NONE_TAKEN,
                settled=DECLINED,
            ),
        ),
        lands=CHOSEN,
    )


def settle(state: State | None = None, **arguments: Any) -> str:
    """What the reader took, as the model reads it: the value, or that none was.

    The answer is where the option stood, so this reads the label back out of the
    options the call carried — a card settles on which one, and the model is owed the
    value rather than a number.

    Args:
        state: Where the question is kept, so the same fork is not put twice.
    """
    if state is not None:
        state.keep(FORKED, str(arguments.get("question", "")))
    options = arguments.get("options") or []
    chosen = str(arguments.get(CHOSEN, ""))
    if chosen.isdigit() and int(chosen) < len(options):
        return str(options[int(chosen)]["label"])
    return NOTHING_CHOSEN
