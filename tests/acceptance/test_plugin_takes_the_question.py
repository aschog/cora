"""The outer test for the story: a plugin answers a question in its field before any
round is spent, and the model is never asked. A question it leaves alone is the model's
as it always was, and the taken turn is in the transcript the model then reads."""

from app_builder import assembled
from cora.ports.chat_model import ModelReply
from cora.ports.host import TAKING, Extension, Host
from fakes import FakeConversations, ScriptedChatModel

FIELD = "quiz"
THREAD = "capitals"
ASKED = "What is the capital of France?"
TAKEN = "Paris."
LEFT = "And how do I get there?"
MODELLED = "By train."


def _capital(question: str) -> str | None:
    return TAKEN if question == ASKED else None


def _quiz(cora: Host) -> None:
    cora.register_instructions("You quiz the reader on capitals.", scope=FIELD)
    cora.register_handler(event=TAKING, handle=_capital, scope=FIELD)


def test_a_plugin_answers_its_own_question_and_the_model_is_never_asked() -> None:
    model = ScriptedChatModel([ModelReply(text=MODELLED)])
    conversations = FakeConversations()
    app = assembled(
        chat_model=model,
        plugins=(Extension(module="quiz", extend=_quiz),),
        conversations=conversations,
    )

    taken = app.agent.answer(ASKED, THREAD)
    left = app.agent.answer(LEFT, THREAD)

    assert taken.answer == TAKEN
    assert left.answer == MODELLED
    assert model.completions == 1, "the taken turn cost no model call"
    assert model.last_messages is not None
    assert [m.content for m in model.last_messages if m.role == "assistant"] == [TAKEN]
    assert [turn.result.answer for turn in conversations.turns(THREAD)] == [
        TAKEN,
        MODELLED,
    ]
