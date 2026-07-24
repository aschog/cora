from core.chat_engine import ChatEngine
from core.chat_model import ModelReply
from fakes import ScriptedChatModel


def test_final_text_reply_becomes_the_answer() -> None:
    model = ScriptedChatModel([ModelReply(text="Hello!")])
    engine = ChatEngine(chat_model=model)

    result = engine.answer("hi")

    assert result.answer == "Hello!"
    assert result.tool_results == ()
