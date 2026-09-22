from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.telegram.bot import Message, answering
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeMemory, ScriptedChatModel
from telegram_fakes import FakeTelegram

CHAT = 4242
DOCUMENT = "protein.md"
PASSAGE = "aim for 1.6 g of protein per kg of bodyweight"
SEED = f"# Protein\n\nFor strength training, {PASSAGE}.\n".encode()
QUESTION = "How much protein should I eat?"
ANSWER = "Your notes say 1.6 g per kg [1]."


def _app() -> App:
    return indexed(
        assembled(
            chat_model=ScriptedChatModel(
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
            ),
            memory=FakeMemory(),
            conversations=FakeConversations(),
        ),
        (DOCUMENT, SEED),
    )


def test_an_allowed_chat_asks_about_a_document_and_the_answer_arrives_there() -> None:
    telegram = FakeTelegram(Message(chat=CHAT, text=QUESTION))

    answering(_app(), telegram, allowed=(CHAT,))

    assert len(telegram.sent) == 1
    chat, text = telegram.sent[0]
    assert chat == CHAT
    assert ANSWER in text
    assert DOCUMENT in text
