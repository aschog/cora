from cora.app.ui.formatting import format_tool_result, ingest_message, numbered_sources
from cora.core.ports.plugin import ToolResult


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
