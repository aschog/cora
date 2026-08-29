"""Where a turn is while it runs: the steps it walks, named as it enters them."""

import pytest

from app_builder import assembled
from cora.domain.chat_result import ChatResult
from cora.ports.chat_model import ModelReply
from fakes import ScriptedChatModel

THREAD = "t1"


def _walked(result: ChatResult) -> list[str]:
    """The steps the turn entered, in the order it entered them."""
    return [
        named for named in (getattr(step, "step", "") for step in result.trace) if named
    ]


@pytest.mark.integration
def test_a_turn_names_the_steps_it_walked() -> None:
    """A turn the user can be told the shape of: admitted, worked, then answered."""
    app = assembled(chat_model=ScriptedChatModel([ModelReply(text="ok")]))

    answered = app.agent.answer("What is cora?", THREAD)

    assert _walked(answered) == ["screen", "work", "answer"]
