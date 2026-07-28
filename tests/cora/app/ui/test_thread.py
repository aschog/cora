from cora.app.ui.thread import thread_to_turns
from cora.core.turn import Turn


def test_thread_to_turns_maps_an_empty_thread_to_nothing() -> None:
    assert thread_to_turns([]) == ()


def test_thread_to_turns_keeps_answered_pairs_in_order() -> None:
    thread = [
        {"role": "user", "content": "I weigh 80 kg."},
        {"role": "assistant", "content": "Noted.", "sources": [], "tool_results": []},
        {"role": "user", "content": "And I'm 1.80 m."},
        {"role": "assistant", "content": "Got it.", "sources": [], "tool_results": []},
    ]

    assert thread_to_turns(thread) == (
        Turn(role="user", text="I weigh 80 kg."),
        Turn(role="assistant", text="Noted."),
        Turn(role="user", text="And I'm 1.80 m."),
        Turn(role="assistant", text="Got it."),
    )


def test_thread_to_turns_drops_an_error_entry_and_the_question_that_caused_it() -> None:
    thread = [
        {"role": "user", "content": "Should I stop taking insulin?"},
        {"role": "assistant", "error": "I can't advise on medication."},
        {"role": "user", "content": "How much protein per day?"},
        {
            "role": "assistant",
            "content": "1.6 g/kg.",
            "sources": [],
            "tool_results": [],
        },
    ]

    assert thread_to_turns(thread) == (
        Turn(role="user", text="How much protein per day?"),
        Turn(role="assistant", text="1.6 g/kg."),
    )


def test_thread_to_turns_drops_a_trailing_unanswered_question() -> None:
    thread = [{"role": "user", "content": "still thinking"}]

    assert thread_to_turns(thread) == ()
