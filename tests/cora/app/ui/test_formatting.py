from cora.app.ui.formatting import (
    DETAIL_CAP,
    ingest_message,
    numbered_sources,
    step_lines,
)
from cora.core.citations import Source
from cora.core.trace import ModelDecision, ToolUse


def test_numbered_sources_renders_each_source_under_its_own_number() -> None:
    assert numbered_sources((Source(1, "a.pdf"), Source(3, "b.md"))) == [
        "[1] a.pdf",
        "[3] b.md",
    ]


def test_numbered_sources_of_nothing_is_empty() -> None:
    assert numbered_sources(()) == []


def test_ingest_message_counts_a_single_chunk_in_the_singular() -> None:
    assert ingest_message("note.md", 1) == "Added note.md — 1 chunk."


def test_ingest_message_pluralises_several_chunks() -> None:
    assert ingest_message("guide.pdf", 12) == "Added guide.pdf — 12 chunks."


def test_ingest_message_reports_no_chunks_as_already_known() -> None:
    assert ingest_message("copy.md", 0) == "copy.md is already in your knowledge base."


def test_a_step_renders_as_its_summary() -> None:
    assert step_lines(ModelDecision(tools=("add",))) == ["**Decided to call add**"]


def test_a_failed_step_is_marked_as_failed() -> None:
    failed = ToolUse(name="add", outcome="unknown tool 'add'", failed=True)

    assert step_lines(failed) == ["⚠️ **add() → unknown tool 'add'**"]


def test_a_steps_detail_follows_it_as_a_block() -> None:
    used = ToolUse(name="search", outcome="1 passage from a.md", detail="[1] a.md: x")

    assert step_lines(used) == [
        "**search() → 1 passage from a.md**",
        "```text\n[1] a.md: x\n```",
    ]


def test_a_detail_already_in_the_summary_is_not_repeated() -> None:
    assert step_lines(ToolUse(name="add", outcome="3", detail="3")) == ["**add() → 3**"]


def test_a_long_detail_is_cut_short() -> None:
    used = ToolUse(name="search", outcome="1 passage", detail="p" * (DETAIL_CAP + 50))

    [_, block] = step_lines(used)
    assert block.count("p") == DETAIL_CAP
    assert block.endswith("…\n```")
