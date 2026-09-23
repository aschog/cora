import pytest

from cora.engine import keeping
from cora.engine.host import PluginHost
from cora.plugins.ask import extend
from cora.plugins.ask.fork import (
    ASK_TOOL_NAME,
    CHOSEN,
    NONE_TAKEN,
    NOTHING_CHOSEN,
    card_of_fork,
    settle,
)
from cora.ports.host import TOOL
from cora.ports.plugin import Tool, ToolRefusal
from fakes import host_for

ASKED = "Which bodyweight should I treat as current?"
OPTIONS = [
    {"label": "77 kg", "note": "intake form, 17 Aug"},
    {"label": "75 kg", "note": "coach notes, February"},
]


def test_the_card_offers_one_action_per_option_a_way_out_and_says_where_it_lands() -> (
    None
):
    card = card_of_fork(
        {"question": ASKED, "options": OPTIONS, "decline": "Don't use any of them"}
    )

    assert card.prompt == ASKED
    assert card.fields == ()
    assert [(action.label, action.answer, action.note) for action in card.actions] == [
        ("77 kg", "0", "intake form, 17 Aug"),
        ("75 kg", "1", "coach notes, February"),
        ("Don't use any of them", NONE_TAKEN, ""),
    ]
    assert card.lands == CHOSEN


def test_a_fork_with_one_way_out_of_it_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_of_fork({"question": ASKED, "options": [{"label": "75 kg"}]})


def test_a_call_with_no_options_is_refused_in_words_the_model_can_read() -> None:
    with pytest.raises(ToolRefusal) as refused:
        card_of_fork({"question": ASKED})

    assert "options" in str(refused.value)


def test_the_tool_says_which_option_was_taken() -> None:
    assert settle(question=ASKED, options=OPTIONS, chosen="1") == "75 kg"


@pytest.mark.parametrize("taken", [NONE_TAKEN, ""])
def test_the_way_out_makes_the_tool_say_nothing_was_chosen(taken: str) -> None:
    assert settle(question=ASKED, options=OPTIONS, chosen=taken) == NOTHING_CHOSEN
    assert settle(question=ASKED, options=OPTIONS) == NOTHING_CHOSEN


def _fork(host: PluginHost) -> Tool:
    extend(host)
    [fork] = [
        entry.value
        for entry in host.registered
        if entry.kind == TOOL and entry.value.name == ASK_TOOL_NAME
    ]
    return fork


def test_the_same_fork_asked_twice_in_a_conversation_is_refused_the_second_time() -> (
    None
):
    fork = _fork(host_for("cora.plugins.ask"))
    arguments = {"question": ASKED, "options": OPTIONS}
    kept: dict = {}

    asks = fork.asks
    assert asks is not None
    with keeping.bound(kept):
        assert asks(arguments) is not None, "the first time, the card stands"
        fork.run(question=ASKED, options=OPTIONS, chosen="1")
        with pytest.raises(ToolRefusal, match="already"):
            asks(arguments)
        assert asks({**arguments, "question": "Which height?"}) is not None


def test_two_options_of_one_label_are_told_apart_by_what_they_answer_with() -> None:
    card = card_of_fork({"question": ASKED, "options": [{"label": "75 kg"}] * 2})

    taken = [action.answer for action in card.actions]
    assert len(set(taken)) == len(taken), "each way off a card is its own answer"
    assert settle(
        question=ASKED, options=[{"label": "75 kg"}] * 2, chosen=taken[1]
    ) == ("75 kg")


def test_an_option_labelled_like_the_way_out_is_still_a_choice() -> None:
    options = [{"label": NONE_TAKEN}, {"label": "75 kg"}]
    card = card_of_fork({"question": ASKED, "options": options})

    chosen = card.actions[0].answer

    assert settle(question=ASKED, options=options, chosen=chosen) == NONE_TAKEN
