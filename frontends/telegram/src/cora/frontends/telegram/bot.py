"""The chat's side of cora: one loop over the messages a bot is sent.

What the Bot API is reached through is a parameter, because a turn answered into a chat
is the part worth testing and a socket is not.
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from cora.app.assembly import App, LiveApp
from cora.domain.card import ActionOffered, Answer, Card
from cora.domain.chat_result import ChatResult
from cora.domain.decision import Pending, TurnPaused
from cora.domain.errors import CoreError

log = logging.getLogger(__name__)

CEILING = 4096
WENT_WRONG = "Something went wrong answering that. Please try again."
PICK_A_NUMBER = "Reply with a number from 1 to {most}."
NOT_A_WAY_OFF = "That is not one of the choices. " + PICK_A_NUMBER


@dataclass(frozen=True)
class Message:
    chat: int
    text: str


class Telegram(Protocol):
    """The two calls the bot is written against: what arrived, and what to send back."""

    def messages(self) -> Iterator[Message]: ...

    def send(self, chat: int, text: str) -> None: ...


def answering(
    app: App | LiveApp, telegram: Telegram, *, allowed: tuple[int, ...]
) -> None:
    """Answer every message from a chat this deployment named, until they run out.

    Handed a `LiveApp`, every message is answered by the composition the plugins folder
    describes by then, as the page answers its requests."""
    apps = app.current if isinstance(app, LiveApp) else (lambda: app)
    for message in telegram.messages():
        # Checked before the turn, and the message dropped rather than refused: a bot
        # is found by anyone, and a reply is a way of saying it is there.
        if message.chat not in allowed:
            # The id and not a word of what was said: this is how an operator learns
            # the number to allow, and a stranger's message is not theirs to keep.
            # Loud enough to reach a terminal nobody configured, which is every
            # terminal the bot is started from the first time.
            log.warning("a message from chat %s was not answered", message.chat)
            continue
        thread = str(message.chat)
        try:
            # Both inside: reading the composition loads whatever is in the plugins
            # folder right now, and a folder that will not load is one message's
            # problem rather than the end of the bot for every chat.
            agent = apps().agent
            # The open card is the agent's to know, never this loop's: a bot restarted
            # mid-question picks the chat up where it left off, holding nothing.
            waiting = agent.pending(thread)
            if waiting is None:
                result = agent.answer(message.text, thread)
            elif (settled := taken(waiting.card, message.text)) is not None:
                result = agent.resume(settled, thread)
            else:
                ways = len(ways_off(waiting.card))
                _reply(telegram, message.chat, NOT_A_WAY_OFF.format(most=ways))
                continue
        except TurnPaused as parked:
            _reply(telegram, message.chat, asked(parked.pending))
            continue
        except CoreError as refused:
            _reply(telegram, message.chat, refused.user_message)
            continue
        except Exception:
            # The chat gets a sentence and the operator gets the stack. Keeping the
            # exception out of the chat is only defensible while the log still has it.
            log.exception("the turn failed in a way nobody modelled")
            _reply(telegram, message.chat, WENT_WRONG)
            continue
        _reply(telegram, message.chat, answered(result))


def answered(result: ChatResult) -> str:
    """One turn as a chat reads it: what it wrote, and under it the documents its
    numbers point at. A turn citing nothing is its own text and no more."""
    if not result.citations:
        return result.answer
    named = "\n".join(
        f"[{cited.number}] {cited.document}" for cited in result.citations
    )
    return f"{result.answer}\n\n{named}"


def asked(pending: Pending) -> str:
    """A parked turn as a chat reads it: what it stopped to ask, what it already holds,
    and the ways off it numbers so a reply can name one."""
    card = pending.card
    ways = ways_off(card)
    known = [
        f"{field.name}: {field.value}"
        for field in card.fields
        if field.value is not None
    ]
    numbered = [f"{number}. {_label(way)}" for number, way in enumerate(ways, 1)]
    blocks = [[card.prompt], known, numbered, [PICK_A_NUMBER.format(most=len(ways))]]
    return "\n\n".join("\n".join(block) for block in blocks if block)


def ways_off(card: Card) -> tuple[ActionOffered, ...]:
    """The actions a chat can take as the card stands.

    One held closed until a required value is written is no way off for a reader with
    nowhere to write it, so it is not offered rather than offered and refused."""
    filled = all(field.value is not None for field in card.fields if field.required)
    return tuple(action for action in card.actions if filled or not action.needs_valid)


def taken(card: Card, reply: str) -> Answer | None:
    """The reply read as one of the card's ways off, or nothing at all.

    A number is what the chat has to answer with, because a label is prose and prose
    read as an answer settles a card on a guess."""
    chosen = reply.strip()
    ways = ways_off(card)
    # `isdecimal` and not `isdigit`: '²' is a digit that `int` refuses to read.
    if not chosen.isdecimal() or not 1 <= int(chosen) <= len(ways):
        return None
    return Answer(
        action=ways[int(chosen) - 1].answer,
        # As they came: what a chat cannot write, it cannot change either.
        values={field.name: field.value for field in card.fields if field.editable},
    )


def parts(text: str) -> Iterator[str]:
    """One message, cut into the ones Telegram will carry — at a line where there is
    one, at a word where there is not, and nothing dropped at the seam."""
    while _units(text) > CEILING:
        fits = _fits(text, CEILING)
        # A separator at the very front would cut a part with nothing in it, and a
        # message of nothing is one the API refuses — so a cut that leaves nothing
        # falls through to the next one rather than straight to the whole window.
        cuts = (text.rfind("\n", 0, fits) + 1, text.rfind(" ", 0, fits) + 1, fits)
        cut = next((at for at in cuts if text[:at].strip()), fits)
        yield text[:cut]
        text = text[cut:]
    yield text


def _label(action: ActionOffered) -> str:
    return f"{action.label} — {action.note}" if action.note else action.label


def _reply(telegram: Telegram, chat: int, text: str) -> None:
    for part in parts(text):
        telegram.send(chat, part)


def _units(text: str) -> int:
    # What Telegram counts, which is not what `len` counts: anything outside the basic
    # plane — an emoji, most of them — is two of these and one of those.
    return len(text.encode("utf-16-le")) // 2


def _fits(text: str, ceiling: int) -> int:
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if _units(text[:middle]) <= ceiling:
            low = middle
        else:
            high = middle - 1
    return low
