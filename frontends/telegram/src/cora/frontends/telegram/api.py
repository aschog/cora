"""The Bot API, as this frontend reaches it: long polling out, one message back.

Telegram is polled rather than subscribed to, because a webhook wants a public address
and cora runs on a machine that has none.
"""

import logging
import time
from collections.abc import Iterator
from typing import Any

import httpx

from cora.frontends.telegram.bot import Message

API = "https://api.telegram.org"
# Under the 50 seconds the Bot API clamps a poll to, and long enough that an idle bot
# costs one request a half-minute rather than one a second.
POLL_SECONDS = 30
AFTER_A_DROP = 3.0
# The read has to outlast the poll the server is holding open; the connect does not,
# and a dead host should be found out in seconds rather than in half a minute.
CONNECT_SECONDS = 5.0
PATIENCE = httpx.Timeout(CONNECT_SECONDS, read=POLL_SECONDS + 10)
# Asked for on every poll rather than once: the Bot API remembers the last list given
# and would otherwise keep delivering whatever a previous run asked for.
ONLY_MESSAGES = ["message"]

BLOCKED = 403
TOO_MANY = 429
MOST_WAITS = 3
LONGEST_WAIT = 60.0
REDACTED = "bot<token>"

log = logging.getLogger(__name__)


class BotApi:
    """One bot account, polled for what it was sent and called to answer.

    The offset is this object's: an update is acknowledged by asking for the one after
    it, so a message read once is never read again — including one nothing was done
    about, which is what keeps a chat nobody named from being polled forever.
    """

    def __init__(
        self,
        token: str,
        *,
        client: httpx.Client | None = None,
        api: str = API,
    ) -> None:
        self._token = token
        self._api = api
        self._client = client or httpx.Client(timeout=PATIENCE)
        self._offset = 0

    def messages(self) -> Iterator[Message]:
        """Every text message the bot is sent, as it arrives, for as long as it runs."""
        while True:
            for update in self._polled():
                self._offset = update["update_id"] + 1
                if (message := _text_message(update)) is not None:
                    yield message

    def send(self, chat: int, text: str) -> None:
        """One message into one chat, as it was written: no parse mode, so nothing in
        it has to be escaped and nothing in it is read as markup.

        What goes wrong with one chat is dropped rather than raised — a reader who
        blocked the bot, a rate that outlasts the waits, a connection that went while
        the reply was on its way. None of it is the end of the bot for everybody else,
        and there is nobody to report it to but the log.
        """
        if not text.strip():
            return
        try:
            self._call("sendMessage", {"chat_id": chat, "text": text})
        except httpx.TransportError:
            log.warning("the reply to chat %s dropped on its way out", chat)
        except httpx.HTTPStatusError as refused:
            if refused.response.status_code not in (BLOCKED, TOO_MANY):
                raise
            log.warning(
                "chat %s did not take the message: %s",
                chat,
                refused.response.status_code,
            )

    def _polled(self) -> list[dict[str, Any]]:
        try:
            return self._call(
                "getUpdates",
                {
                    "offset": self._offset,
                    "timeout": POLL_SECONDS,
                    "allowed_updates": ONLY_MESSAGES,
                },
            )
        except httpx.TransportError:
            # A network that dropped, not an answer that refused: waited out and asked
            # again. Nothing was confirmed, so nothing was lost. A refusal — a revoked
            # token, a second bot on the same account — is a status code, and that ends
            # the run where somebody will read it.
            log.warning("the poll dropped, asking again in %ss", AFTER_A_DROP)
            time.sleep(AFTER_A_DROP)
            return []
        except httpx.HTTPStatusError as refused:
            # Except this one: being asked to wait longer than the waits above allow
            # is still a rate, and a rate passes.
            if refused.response.status_code != TOO_MANY:
                raise
            log.warning("the poll is rate limited, asking again in %ss", AFTER_A_DROP)
            time.sleep(AFTER_A_DROP)
            return []

    def _call(self, method: str, payload: dict[str, Any]) -> Any:
        response = self._sent(method, payload)
        # Waited out as often as the ceiling allows rather than once: one wait that
        # came back short leaves the call refused, and a refusal ends the run.
        for _ in range(MOST_WAITS):
            if response.status_code != TOO_MANY:
                break
            time.sleep(min(_retry_after(response), LONGEST_WAIT))
            response = self._sent(method, payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as refused:
            # The token is in the URL, and httpx puts the URL in the message: raised as
            # it arrives, a refused call prints the bot's password to the log.
            raise httpx.HTTPStatusError(
                _redacted(str(refused), self._token),
                request=refused.request,
                response=refused.response,
            ) from None
        return response.json()["result"]

    def _sent(self, method: str, payload: dict[str, Any]) -> httpx.Response:
        return self._client.post(f"{self._api}/bot{self._token}/{method}", json=payload)


def _retry_after(response: httpx.Response) -> float:
    # Sending an answer in parts runs into the per-chat rate on the ordinary path, so
    # what it asks for is waited out rather than raised. Read defensively: a 429 from
    # something between here and Telegram is a page, not a body with a number in it.
    try:
        asked = response.json().get("parameters", {}).get("retry_after")
    except ValueError:
        asked = None
    return float(asked) if isinstance(asked, int | float) else AFTER_A_DROP


def _redacted(message: str, token: str) -> str:
    return message.replace(f"bot{token}", REDACTED)


def _text_message(update: dict[str, Any]) -> Message | None:
    # A photo, a sticker, a chat somebody joined, a message edited after the fact:
    # an update with no text is not one to answer. The offset above takes it either way.
    message = update.get("message") or {}
    text = message.get("text")
    chat = (message.get("chat") or {}).get("id")
    if not isinstance(text, str) or not isinstance(chat, int):
        return None
    return Message(chat=chat, text=text)
