"""The process the deployment runs: cora answering the chats its bot was told to.

Everything the bot needs of its own is read and refused first, before a model is
loaded or a store is opened — a deployment that cannot answer anybody costs the
operator a sentence rather than the wait for an app it will not use.
"""

import logging
import os
import sys
from collections.abc import Mapping

from cora.app.assembly import live
from cora.app.config import Config
from cora.domain.errors import ConfigurationError, CoreError
from cora.frontends.telegram.api import BotApi
from cora.frontends.telegram.bot import answering

TOKEN = "CORA_TELEGRAM_TOKEN"
CHATS = "CORA_TELEGRAM_CHATS"
HTTP_LOGGER = "httpx"


def token(env: Mapping[str, str]) -> str:
    """The bot account to answer from.

    Raises:
        ConfigurationError: No token is set, so there is no bot to be.
    """
    named = env.get(TOKEN, "").strip()
    if not named:
        raise ConfigurationError(
            f"{TOKEN} is not set, so there is no bot to answer as."
        )
    return named


def allowed(env: Mapping[str, str]) -> tuple[int, ...]:
    """The chats this deployment answers, and nobody else.

    A bot is found by anyone who has its name, so an empty list is refused rather than
    read as "everybody": the documents behind it are the operator's own.

    Raises:
        ConfigurationError: No chat is named, or one of them is not a chat id.
    """
    named = [chat.strip() for chat in env.get(CHATS, "").split(",") if chat.strip()]
    if not named:
        raise ConfigurationError(
            f"{CHATS} names no chat, and a bot that answers nobody is not started."
        )
    for chat in named:
        if not chat.removeprefix("-").isdigit():
            raise ConfigurationError(f"{CHATS} holds {chat!r}, which is not a chat id.")
    return tuple(int(chat) for chat in named)


def serve() -> None:
    """Run the bot until it is stopped, or refuse to start and say why."""
    # The token is in every URL the client builds, and the client writes one line per
    # request at INFO. Nothing turns that on today, and a bot left running unattended
    # under somebody's log capture is exactly where it would be turned on.
    logging.getLogger(HTTP_LOGGER).setLevel(logging.WARNING)
    try:
        chats = allowed(os.environ)
        bot = BotApi(token(os.environ))
        app = live(Config.from_env())
    except CoreError as refused:
        # Written here rather than left to `SystemExit` to carry: an exit whose argument
        # is a string is only printed if nothing catches it on the way out.
        print(f"cora cannot start: {refused.user_message}", file=sys.stderr)
        raise SystemExit(1) from None
    answering(app, bot, allowed=chats)


if __name__ == "__main__":
    serve()
