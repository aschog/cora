from app_builder import indexed
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.telegram.bot import CEILING, Message, answering
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from telegram_fakes import ALLOWED, FakeTelegram, chatting

DOCUMENT = "protein.md"
SEED = b"# Protein\n\nFor strength training, aim for 1.6 g per kg of bodyweight.\n"
ANSWER = "Your notes say 1.6 g per kg [1]."


def _citing() -> FakeTelegram:
    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=SEARCH_TOOL_NAME,
                        arguments={"query": "protein"},
                        call_id="call-1",
                    ),
                )
            ),
            ModelReply(text=ANSWER),
        ]
    )
    telegram = FakeTelegram(Message(ALLOWED, "How much protein?"))
    answering(
        indexed(chatting(chat_model=model), (DOCUMENT, SEED)),
        telegram,
        allowed=(ALLOWED,),
    )
    return telegram


def test_an_answer_is_the_text_the_turn_wrote() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "Why?"))

    answering(chatting(answers="Sleep, not volume."), telegram, allowed=(ALLOWED,))

    assert telegram.texts == ["Sleep, not volume."]


def test_the_documents_an_answer_cites_are_named_under_it() -> None:
    sent = _citing().texts[0]

    assert sent.startswith(ANSWER)
    assert f"[1] {DOCUMENT}" in sent


def test_an_answer_citing_nothing_is_sent_with_nothing_under_it() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "Why?"))

    answering(chatting(answers="Sleep."), telegram, allowed=(ALLOWED,))

    assert telegram.texts == ["Sleep."]


def test_an_answer_past_the_ceiling_is_sent_in_parts_whole() -> None:
    written = "\n".join(f"line {number}" for number in range(1000))
    telegram = FakeTelegram(Message(ALLOWED, "Tell me everything"))

    answering(chatting(answers=written), telegram, allowed=(ALLOWED,))

    assert len(telegram.texts) > 1
    assert all(len(part.encode("utf-16-le")) // 2 <= CEILING for part in telegram.texts)
    assert "".join(telegram.texts) == written


def test_a_part_is_cut_at_a_line_rather_than_mid_word() -> None:
    written = "\n".join("x" * 100 for _ in range(200))
    telegram = FakeTelegram(Message(ALLOWED, "Tell me everything"))

    answering(chatting(answers=written), telegram, allowed=(ALLOWED,))

    assert all(part.endswith("\n") for part in telegram.texts[:-1])


def test_a_part_is_cut_at_a_word_where_the_answer_has_no_lines() -> None:
    written = " ".join("word" for _ in range(2000))
    telegram = FakeTelegram(Message(ALLOWED, "Tell me everything"))

    answering(chatting(answers=written), telegram, allowed=(ALLOWED,))

    assert len(telegram.texts) > 1
    assert all(part.endswith(" ") for part in telegram.texts[:-1])
    assert "".join(telegram.texts) == written


def test_an_answer_with_nowhere_to_cut_is_still_cut() -> None:
    written = "x" * 9000
    telegram = FakeTelegram(Message(ALLOWED, "Tell me everything"))

    answering(chatting(answers=written), telegram, allowed=(ALLOWED,))

    assert len(telegram.texts) == 3
    assert "".join(telegram.texts) == written


def test_the_ceiling_counts_what_telegram_counts() -> None:
    written = "\U0001f600" * 3000
    telegram = FakeTelegram(Message(ALLOWED, "Tell me everything"))

    answering(chatting(answers=written), telegram, allowed=(ALLOWED,))

    assert len(telegram.texts) == 2
    assert all(len(part.encode("utf-16-le")) // 2 <= CEILING for part in telegram.texts)
    assert "".join(telegram.texts) == written


def test_an_answer_that_opens_with_a_line_break_sends_no_blank_part() -> None:
    written = "\n" + "word " * 2000
    telegram = FakeTelegram(Message(ALLOWED, "Tell me everything"))

    answering(chatting(answers=written), telegram, allowed=(ALLOWED,))

    assert all(part.strip() for part in telegram.texts)
    assert all(part.endswith(" ") for part in telegram.texts[:-1])
    assert "".join(telegram.texts) == written
