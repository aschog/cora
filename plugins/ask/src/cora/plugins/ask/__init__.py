from cora.ports.host import Host

from .fork import ASK_SCHEMA, ASK_TOOL_NAME, FORK_DESCRIPTION, card_of_fork, settle
from .form import (
    ASK_FOR_SCHEMA,
    ASK_FOR_TOOL_NAME,
    FORM_DESCRIPTION,
    card_of_form,
    fill,
)

RULES = (
    f"Call the {ASK_TOOL_NAME} tool when what you already know about this user holds "
    "the same fact at two or more different values, nothing says which is current, and "
    "the answer depends on it. Offer the values you found, one option each, and say "
    "where each came from. Ask once, then answer with what you are given — never guess "
    "which of them was meant.\n\n"
    f"Call the {ASK_FOR_TOOL_NAME} tool the moment an answer turns on two or more "
    "values you do not have and cannot look up — where they are flying from, which "
    "days, what they want to spend. Name those values as fields and let the form ask "
    "for them, rather than asking for them in your answer: an answer that asks for "
    "four things costs the user a turn and answers none of them. Where one value is "
    "all you are missing, ask for it in your answer instead — a form of one box is a "
    "stop the sentence already made. Ask for what the answer turns on and no more, "
    "and mark a field required only where you cannot proceed without it."
)


def extend(cora: Host) -> None:
    """Two tools that stop the turn, system-wide, and the rule for when to call each.

    Both are gathering tools: the card each declares is what the gate puts to the
    reader, and the tool then runs on the answer — so nothing here pauses anything, and
    the engine keeps no step for asking. The fork's card names where the option taken
    lands, which is how a choice between buttons reaches a tool at all."""
    cora.register_tool(
        name=ASK_TOOL_NAME,
        description=FORK_DESCRIPTION,
        parameter_schema=ASK_SCHEMA,
        run=lambda **arguments: settle(cora.state, **arguments),
        asks=lambda arguments: card_of_fork(arguments, cora.state),
    )
    cora.register_tool(
        name=ASK_FOR_TOOL_NAME,
        description=FORM_DESCRIPTION,
        parameter_schema=ASK_FOR_SCHEMA,
        run=fill,
        asks=card_of_form,
    )
    cora.register_instructions(RULES)
