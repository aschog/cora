"""What cora refuses before a turn starts, subscribed the way a plugin subscribes."""

from cora.ports.host import SCREENING, Host

CORA = "cora"
"""The module name cora's own contributions are registered under. It is a plugin of
itself here: there is one door into a turn, and cora goes through it too."""
MAX_INPUT_CHARS = 4000
"""What a question may run to. Beside the handler that enforces it, as the fact bound is
beside the tool it sizes."""


def refuse_nothing_to_answer(question: str) -> str | None:
    """Refuse a question that is empty or only whitespace."""
    return None if question.strip() else "Please enter a question."


def refuse_too_long(question: str) -> str | None:
    """Refuse a question over `MAX_INPUT_CHARS`, naming the cap.

    A cap so that a paste of a whole document is refused as input rather than answered
    as a question.
    """
    if len(question) <= MAX_INPUT_CHARS:
        return None
    return f"Your message is too long — the limit is {MAX_INPUT_CHARS} characters."


def extend(cora: Host) -> None:
    """Register what cora asks of any input, whatever it was asked to be.

    Screening for injection is not here: it is a plugin, and so something a deployment
    adds. What is here is system-wide, and registered first, so no plugin's handler is
    ever handed a question cora would have refused outright.
    """
    cora.register_handler(event=SCREENING, handle=refuse_nothing_to_answer)
    cora.register_handler(event=SCREENING, handle=refuse_too_long)
