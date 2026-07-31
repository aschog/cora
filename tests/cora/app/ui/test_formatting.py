from cora.app.ui.formatting import ingest_message, numbered_sources
from cora.core.services.chat_engine import Source


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
