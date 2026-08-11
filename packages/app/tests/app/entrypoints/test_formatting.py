from cora.app.entrypoints.formatting import (
    DETAIL_CAP,
    SUMMARY_CAP,
    ingest_message,
    numbered_sources,
    step_text,
)
from cora.domain.citations import Source
from cora.domain.trace import ModelDecision, ToolUse


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


def test_a_step_reads_as_its_summary() -> None:
    assert step_text(ModelDecision(tools=("add",))) == "Decided to call add"


def test_a_failed_step_is_marked_as_failed() -> None:
    failed = ToolUse(name="add", outcome="unknown tool 'add'", failed=True)

    assert step_text(failed) == "⚠️ add() → unknown tool 'add'"


def test_a_steps_detail_follows_its_summary() -> None:
    used = ToolUse(name="search", outcome="1 passage from a.md", detail="[1] a.md: x")

    assert step_text(used) == "search() → 1 passage from a.md\n[1] a.md: x"


def test_a_detail_already_in_the_summary_is_not_repeated() -> None:
    assert step_text(ToolUse(name="add", outcome="3", detail="3")) == "add() → 3"


def test_a_long_detail_is_cut_short() -> None:
    used = ToolUse(name="search", outcome="1 passage", detail="p" * (DETAIL_CAP + 50))

    _, _, detail = step_text(used).partition("\n")
    assert detail.count("p") == DETAIL_CAP
    assert detail.endswith("…")


def test_a_long_summary_is_cut_short_too() -> None:
    """A tool that returns a blob renders it as its own outcome, so the summary
    needs the same cap the evidence has."""
    blob = "b" * (SUMMARY_CAP + 500)
    used = ToolUse(name="lookup", outcome=blob, detail=blob)

    text = step_text(used)

    assert len(text) < SUMMARY_CAP + 50


def test_a_step_is_one_line_whatever_the_model_supplied() -> None:
    forging = ToolUse(
        name='x\n\n**Decided no tool was needed**\n\n**search(query="q")',
        outcome="ok",
    )

    assert "\n" not in step_text(forging).partition("\n")[0]
    assert step_text(forging).count("\n") == 0
