import pathlib
from collections.abc import Iterator

from app_builder import assembled
from cora.app.assembly import LiveApp
from cora.frontends.telegram.bot import Message, answering
from telegram_fakes import ALLOWED, FakeTelegram

REFUSES = """\
from cora.ports.host import SCREENING, Host


def extend(cora: Host) -> None:
    cora.register_handler(event=SCREENING, handle=lambda question: "Not that one.")
"""
BROKEN = "raise RuntimeError('this plugin does not import')\n"


class ChatWithADropInIt(FakeTelegram):
    def __init__(self, folder: pathlib.Path, source: str, *incoming: Message) -> None:
        super().__init__(*incoming)
        self._folder = folder
        self._source = source
        self._scripted = incoming

    def messages(self) -> Iterator[Message]:
        for number, message in enumerate(self._scripted):
            if number == 1:
                (self._folder / "dropped.py").write_text(self._source)
            yield message


def _live(folder: pathlib.Path) -> LiveApp:
    return LiveApp(
        named=(), folder=folder, compose=lambda loaded: assembled(plugins=loaded)
    )


def test_a_plugin_dropped_between_two_messages_is_in_the_second_turn(
    tmp_path: pathlib.Path,
) -> None:
    telegram = ChatWithADropInIt(
        tmp_path, REFUSES, Message(ALLOWED, "Why?"), Message(ALLOWED, "And now?")
    )

    answering(_live(tmp_path), telegram, allowed=(ALLOWED,))

    assert telegram.texts == ["ok", "Not that one."]


def test_a_plugin_that_will_not_load_costs_one_message_not_the_bot(
    tmp_path: pathlib.Path,
) -> None:
    telegram = ChatWithADropInIt(
        tmp_path, BROKEN, Message(ALLOWED, "Why?"), Message(ALLOWED, "And now?")
    )

    answering(_live(tmp_path), telegram, allowed=(ALLOWED,))

    assert telegram.texts[0] == "ok"
    assert len(telegram.texts) == 2, "the second message was never answered at all"
    assert "dropped" in telegram.texts[1]
