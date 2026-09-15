from cora.frontends.telegram.bot import Message, answering
from cora.ports.chat_model import ModelReply
from fakes import FakeConversations, ScriptedChatModel
from telegram_fakes import ALLOWED, STRANGER, FakeTelegram, chatting

FIRST = "What did I say about squats?"
SECOND = "And what about deadlifts?"


def test_one_chat_is_one_thread_and_the_second_question_knows_the_first() -> None:
    model = ScriptedChatModel([ModelReply(text="squats"), ModelReply(text="deadlifts")])
    conversations = FakeConversations()
    telegram = FakeTelegram(Message(ALLOWED, FIRST), Message(ALLOWED, SECOND))

    answering(
        chatting(chat_model=model, conversations=conversations),
        telegram,
        allowed=(ALLOWED,),
    )

    recorded = conversations.turns(str(ALLOWED))
    assert [turn.question for turn in recorded] == [FIRST, SECOND]
    said = [message.content for message in model.last_messages or ()]
    assert any(FIRST in content for content in said)


def test_two_chats_do_not_read_each_other() -> None:
    conversations = FakeConversations()
    telegram = FakeTelegram(Message(ALLOWED, FIRST), Message(STRANGER, SECOND))

    answering(
        chatting(conversations=conversations),
        telegram,
        allowed=(ALLOWED, STRANGER),
    )

    assert [turn.question for turn in conversations.turns(str(ALLOWED))] == [FIRST]
    assert [turn.question for turn in conversations.turns(str(STRANGER))] == [SECOND]
    # The destination and not just the thread: an answer delivered to the wrong chat
    # is the one failure a one-chat test can never see.
    assert [chat for chat, _ in telegram.sent] == [ALLOWED, STRANGER]
