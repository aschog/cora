from cora.app.ui.formatting import (
    format_tool_result,
    ingest_message,
    numbered_sources,
    thread_to_turns,
)
from cora.core.ports.plugin import ToolResult
from cora.core.turn import Turn


def test_numbered_sources_renders_bracketed_numbers_in_order() -> None:
    assert numbered_sources(("a.pdf", "b.md")) == ["[1] a.pdf", "[2] b.md"]


def test_numbered_sources_of_nothing_is_empty() -> None:
    assert numbered_sources(()) == []


def test_ingest_message_counts_a_single_chunk_in_the_singular() -> None:
    assert ingest_message("note.md", 1) == "Added note.md — 1 chunk."


def test_ingest_message_pluralises_several_chunks() -> None:
    assert ingest_message("guide.pdf", 12) == "Added guide.pdf — 12 chunks."


def test_ingest_message_reports_no_chunks_as_already_known() -> None:
    assert ingest_message("copy.md", 0) == "copy.md is already in your knowledge base."


def test_format_tool_result_shows_the_error_message() -> None:
    result = ToolResult(call_id="c1", error="Unknown tool 'tdee'.")

    assert format_tool_result(result) == "Unknown tool 'tdee'."


def test_format_tool_result_shows_a_string_payload_as_is() -> None:
    result = ToolResult(call_id="c1", payload="2500 kcal")

    assert format_tool_result(result) == "2500 kcal"


def test_format_tool_result_renders_other_payloads_as_json() -> None:
    result = ToolResult(call_id="c1", payload={"tdee": 2500, "unit": "kcal"})

    assert format_tool_result(result) == '{"tdee": 2500, "unit": "kcal"}'


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
