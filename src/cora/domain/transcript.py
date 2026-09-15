"""What the model is shown of a conversation, which is less than the thread holds."""

from collections.abc import Sequence

from cora.ports.chat_model import Message

WORDS_SPOKEN = ("user", "assistant")


def prompt_from(
    *,
    brief: str,
    transcript: Sequence[Message],
    turn_start: int,
    max_history_turns: int,
) -> tuple[Message, ...]:
    """What this turn's model call sees.

    The brief, then what was said before it, then the turn so far verbatim. The thread
    keeps everything; the prompt is a projection of it, so a conversation grows without
    the prompt growing with it — and the brief is stated once however long the thread
    runs.
    """
    said = _distilled(transcript[:turn_start])
    recent = said[max(len(said) - max_history_turns, 0) :]
    return (
        Message(role="system", content=brief),
        *recent,
        *transcript[turn_start:],
    )


def _distilled(past: Sequence[Message]) -> tuple[Message, ...]:
    return tuple(
        Message(role=message.role, content=message.content)
        for message in past
        if message.role in WORDS_SPOKEN and message.content and not message.tool_calls
    )
