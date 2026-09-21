"""The outer test for the story: a right answer gets the next word from the drill.

The model puts the first word and is then never asked while the answers keep coming
right — the drill records each one and puts the next. What does reach the model, a hint
asked for, arrives with the taken words in the transcript it reads."""

from typing import Any

import pytest

from app_builder import assembled
from cora.engine.plugin_registry import load_plugin
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeFiles, FakeStore, ScriptedChatModel

FIELD = "vocab"
THREAD = "einheit"
LISTED = "unit.md"
PAIRS = {"Hund": "dog", "Katze": "cat", "Haus": "house", "Baum": "tree"}
LIST = "| Deutsch | English |\n| --- | --- |\n" + "".join(
    f"| {german} | {english} |\n" for german, english in PAIRS.items()
)
# What the model writes after the first word was put: a word from nowhere, which the
# check on the answer replaces with the word on the table — so the test learns which
# word a shuffled pass put first without scripting the shuffle.
INVENTED = "Erfunden"
HINT = "Klingt wie eine Dogge, die dir die Hand gibt. Welches Wort ist es?"


def _calling(*calls: tuple[str, dict[str, Any]]) -> ModelReply:
    return ModelReply(
        tool_calls=tuple(
            ToolCall(name=tool, arguments=arguments, call_id=tool)
            for tool, arguments in calls
        )
    )


@pytest.mark.xfail(strict=True)
def test_right_answers_get_the_next_word_without_the_model_being_asked() -> None:
    model = ScriptedChatModel(
        [
            _calling(
                ("german_side", {"name": LISTED, "side": "left"}),
                ("next_word", {}),
            ),
            ModelReply(text=INVENTED),
            ModelReply(text=HINT),
        ]
    )
    app = assembled(
        chat_model=model,
        plugins=(load_plugin("cora.plugins.vocab"),),
        conversations=FakeConversations(),
        store=FakeStore(),
        files=FakeFiles({(FIELD, LISTED): LIST}),
    )

    put = [app.agent.answer("Los.", THREAD).answer]
    assert put[0] in PAIRS
    asked = model.completions

    for _ in range(3):
        assert put[-1] in PAIRS, f"not a word of the list: {put[-1]!r}"
        put.append(app.agent.answer(PAIRS[put[-1]], THREAD).answer)

    assert all(word in PAIRS for word in put)
    assert len(set(put)) == 4, "every word once: a right answer moves the pass on"
    assert model.completions == asked, "a right answer cost no model call"

    hinted = app.agent.answer("h", THREAD)

    assert hinted.answer == HINT
    assert model.completions == asked + 1
    assert model.last_messages is not None
    said = [message.content for message in model.last_messages]
    assert all(word in said for word in put[1:]), "the model read the taken words"
    assert all(PAIRS[word] in said for word in put[:3]), "and the answers given"
