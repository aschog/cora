from cora.domain.transcript import prompt_from
from cora.ports.chat_model import Message, Role
from cora.ports.plugin import ToolCall

BRIEF = "You are a coach."


def _said(*texts: str) -> list[Message]:
    roles: tuple[Role, ...] = ("user", "assistant")
    return [
        Message(role=roles[index % 2], content=text) for index, text in enumerate(texts)
    ]


def _prompt(
    transcript: list[Message], turn_start: int, max_history_turns: int = 20
) -> tuple[Message, ...]:
    return prompt_from(
        brief=BRIEF,
        transcript=transcript,
        turn_start=turn_start,
        max_history_turns=max_history_turns,
    )


def _past(sent: tuple[Message, ...]) -> list[str]:
    return [message.content for message in sent[1:-1]]


def test_the_brief_leads_and_the_current_question_ends_the_prompt() -> None:
    sent = _prompt(_said("What is BMI?"), turn_start=0)

    assert sent[0] == Message(role="system", content=BRIEF)
    assert sent[-1] == Message(role="user", content="What is BMI?")


def test_a_previous_turn_arrives_as_its_user_and_assistant_words() -> None:
    transcript = [*_said("I weigh 80 kg.", "Noted."), *_said("What was my weight?")]

    sent = _prompt(transcript, turn_start=2)

    assert [message.role for message in sent] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert _past(sent) == ["I weigh 80 kg.", "Noted."]


def test_a_previous_turns_tool_traffic_stays_in_the_thread() -> None:
    """Old tool calls, their results and the gate's reminders are the thread's
    record, not the next turn's prompt — which is what `Turn(role, text)` meant
    before the thread held anything."""
    call = ToolCall(name="search_documents", arguments={"query": "x"}, call_id="c1")
    transcript = [
        Message(role="user", content="What do my notes say?"),
        Message(role="assistant", content="", tool_calls=(call,)),
        Message(role="tool", content="[1] note.md: protein", tool_call_id="c1"),
        Message(role="system", content="You answered without searching."),
        Message(role="assistant", content="Your notes say protein [1]."),
        Message(role="user", content="And now?"),
    ]

    sent = _prompt(transcript, turn_start=5)

    assert _past(sent) == ["What do my notes say?", "Your notes say protein [1]."]


def test_the_current_turn_is_sent_verbatim_never_distilled() -> None:
    """Mid-round the model has to see its own tool call and what came back, or it
    cannot continue the round it started."""
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    transcript = [
        Message(role="user", content="Add 1 and 2."),
        Message(role="assistant", content="", tool_calls=(call,)),
        Message(role="tool", content="3", tool_call_id="c1"),
    ]

    sent = _prompt(transcript, turn_start=0)

    assert sent[1:] == tuple(transcript)


def test_previous_turns_beyond_the_cap_drop_the_oldest() -> None:
    transcript = [*_said("oldest", "old", "recent", "newest"), *_said("q")]

    sent = _prompt(transcript, turn_start=4, max_history_turns=2)

    assert _past(sent) == ["recent", "newest"]


def test_previous_turns_shorter_than_the_cap_are_sent_in_full() -> None:
    transcript = [*_said("I weigh 80 kg.", "Noted."), *_said("q")]

    sent = _prompt(transcript, turn_start=2, max_history_turns=5)

    assert _past(sent) == ["I weigh 80 kg.", "Noted."]


def test_previous_turns_exactly_at_the_cap_are_sent_in_full() -> None:
    transcript = [*_said("I weigh 80 kg.", "Noted."), *_said("q")]

    sent = _prompt(transcript, turn_start=2, max_history_turns=2)

    assert _past(sent) == ["I weigh 80 kg.", "Noted."]


def test_an_odd_cap_sends_a_leading_assistant_turn_without_its_question() -> None:
    """The cap counts messages, not exchanges, so an orphan reply is accepted."""
    transcript = [
        *_said("I weigh 80 kg.", "Noted.", "And I am 1.80 m.", "Got it."),
        *_said("q"),
    ]

    sent = _prompt(transcript, turn_start=4, max_history_turns=3)

    assert _past(sent) == ["Noted.", "And I am 1.80 m.", "Got it."]
    assert sent[1].role == "assistant"


def test_a_cap_of_zero_sends_no_previous_turn_at_all() -> None:
    transcript = [*_said("I weigh 80 kg.", "Noted."), *_said("q")]

    sent = _prompt(transcript, turn_start=2, max_history_turns=0)

    assert [message.role for message in sent] == ["system", "user"]


def test_the_cap_never_cuts_the_current_turn() -> None:
    transcript = [
        *_said("old", "older"),
        Message(role="user", content="q"),
        Message(role="assistant", content="", tool_calls=()),
        Message(role="tool", content="3", tool_call_id="c1"),
    ]

    sent = _prompt(transcript, turn_start=2, max_history_turns=0)

    assert [message.role for message in sent] == ["system", "user", "assistant", "tool"]
