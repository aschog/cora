"""The step where a plugin may answer the question before any round is spent."""

from cora.domain.agent_state import AgentState
from cora.domain.trace import HandlerRan
from cora.engine import keeping
from cora.engine.plugin_set import Registry
from cora.engine.scoping import here
from cora.engine.steps import TakeStep, opening
from cora.ports.chat_model import Message
from cora.ports.graph import DONE, ROUNDS
from cora.ports.host import HANDLER, TAKING, Handler, Registration, Subscription

MODULE = "fixture_plugins.quiz"
PLUGIN = "quiz"
FIELD = "quiz"


def _taking(*takers: Handler, scope: str | None = FIELD) -> TakeStep:
    return TakeStep(
        registry=Registry(
            tuple(
                Registration(
                    module=MODULE,
                    kind=HANDLER,
                    value=Subscription(event=TAKING, handle=take),
                    scope=scope,
                )
                for take in takers
            )
        )
    )


def _asked(
    question: str = "q",
    scopes: tuple[str, ...] = (FIELD,),
    kept: dict[str, dict[str, str]] | None = None,
) -> AgentState:
    return {
        "question": question,
        "messages": [Message(role="user", content=question)],
        "turn_start": 0,
        "scopes": list(scopes),
        "kept": kept or {},
    }


def test_what_was_taken_is_this_turns_answer_and_the_trace_names_the_plugin() -> None:
    contributed = _taking(lambda question: "42")(_asked())

    assert contributed["messages"] == [Message(role="assistant", content="42")]
    assert contributed["trace"] == [
        HandlerRan(plugin=MODULE, event=TAKING, outcome="took the question")
    ]


def test_nothing_taken_contributes_no_message() -> None:
    contributed = _taking(lambda question: None)(_asked())

    assert "messages" not in contributed
    assert contributed["trace"] == []


def test_a_handler_is_handed_the_question_in_the_turns_field() -> None:
    seen: list[tuple[str, frozenset[str]]] = []

    def take(question: str) -> str:
        seen.append((question, here()))
        return "ok"

    _taking(take)(_asked("Which one?"))

    assert seen == [("Which one?", frozenset({FIELD}))]


def test_what_is_kept_while_taking_is_contributed_and_what_was_kept_is_read() -> None:
    read: list[str | None] = []

    def take(question: str) -> str:
        read.append(keeping.read(PLUGIN, "note"))
        keeping.keep(PLUGIN, "note", "after")
        return "ok"

    contributed = _taking(take)(_asked(kept={PLUGIN: {"note": "before"}}))

    assert read == ["before"]
    assert contributed["kept"] == {PLUGIN: {"note": "after"}}


def test_a_handler_under_another_field_is_not_offered_the_question() -> None:
    offered: list[str] = []

    def take(question: str) -> str:
        offered.append(question)
        return "ok"

    contributed = _taking(take, scope="other")(_asked())

    assert offered == []
    assert "messages" not in contributed


def test_the_opening_route_leaves_the_rounds_once_this_turn_holds_an_answer() -> None:
    question = Message(role="user", content="q")
    taken = Message(role="assistant", content="42")

    assert opening({"messages": [question, taken], "turn_start": 0}) == DONE
    assert opening({"messages": [question], "turn_start": 0}) == ROUNDS
    # An earlier turn's answer is not this turn's.
    assert opening({"messages": [question, taken, question], "turn_start": 2}) == ROUNDS
