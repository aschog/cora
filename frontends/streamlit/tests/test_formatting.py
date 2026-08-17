from cora.domain.citations import Citation
from cora.domain.trace import ModelDecision, ToolUse
from cora.frontends.streamlit.formatting import (
    CITATION_ANCHOR,
    DETAIL_CAP,
    SUMMARY_CAP,
    answer_html,
    document_html,
    ingest_message,
    numbered_citations,
    step_text,
)


def test_numbered_citations_renders_each_passage_under_its_own_number() -> None:
    """One line per passage, not per document: two passages of one file are two lines,
    which is what tells the reader which number opens which."""
    assert numbered_citations(
        (
            Citation(1, "a.pdf", 0, 5),
            Citation(2, "a.pdf", 40, 50),
            Citation(3, "b.md", 20, 30),
        )
    ) == [
        "[1] a.pdf",
        "[2] a.pdf",
        "[3] b.md",
    ]


def test_numbered_citations_of_nothing_is_empty() -> None:
    assert numbered_citations(()) == []


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


NOTE = Citation(number=1, document="note.md", start=6, end=10)


def test_the_answer_is_rendered_as_the_markdown_it_is() -> None:
    html = answer_html("**Bold** advice:\n\n- first\n- second\n", ())

    assert "<strong>Bold</strong>" in html
    assert html.count("<li>") == 2


def test_a_number_with_a_citation_behind_it_becomes_a_button() -> None:
    html = answer_html("Your notes say so [1].", (NOTE,))

    assert 'data-cite="1"' in html
    assert ">[1]<" in html


def test_a_number_with_no_citation_behind_it_stays_text() -> None:
    """A model can write `[9]` with nothing behind it, and a button that opens nothing
    is worse than the text it replaced."""
    html = answer_html("As [9] says, and [1].", (NOTE,))

    assert 'data-cite="9"' not in html
    assert "[9]" in html
    assert 'data-cite="1"' in html


def test_a_bracketed_number_inside_code_is_left_alone() -> None:
    html = answer_html(
        "Use it like this:\n\n```\nitems[1]\n```\n\nas [1] says.", (NOTE,)
    )

    assert html.count('data-cite="1"') == 1
    assert "items[1]" in html


def test_markup_in_the_answer_is_text_and_never_an_element() -> None:
    """The answer is written by a model reading the user's documents, so a document
    that asks for a script must not get one."""
    html = answer_html("<script>alert(1)</script> and <b>raw</b>", ())

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>" not in html


def test_the_document_is_escaped_so_its_markup_reads_as_text() -> None:
    html = document_html("<script>alert(1)</script> stays", Citation(1, "d.md", 0, 0))

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_the_cited_span_is_marked_and_nothing_else_is() -> None:
    html = document_html("Every gram of protein counts", NOTE)

    assert html.count("<mark") == 1
    assert f'id="{CITATION_ANCHOR.format(number=1)}"' in html
    assert ">gram<" in html


def test_a_span_running_past_the_end_marks_to_the_end() -> None:
    """A span is measured in the text the pane reads, so this needs the two to have
    come apart — text kept by a repair, parsed after the offsets were measured. The pane
    shows what it can rather than raising at the reader."""
    html = document_html("short", Citation(1, "d.md", 2, 500))

    assert ">ort<" in html
    assert html.count("<mark") == 1


def test_a_document_with_no_citation_to_mark_is_still_rendered() -> None:
    html = document_html("plain text", None)

    assert "plain text" in html
    assert "<mark" not in html


OMEGA = Citation(number=2, document="note.md", start=40, end=45)


def test_every_number_in_a_run_becomes_its_own_button() -> None:
    """Numbering is per passage now, so citing two passages at once is ordinary. The
    domain reads every number in a run — `cited_numbers` — and a button the reader can
    press has to follow it, or the second passage is listed and unopenable."""
    html = answer_html("Both notes agree [1][2].", (NOTE, OMEGA))

    assert 'data-cite="1"' in html
    assert 'data-cite="2"' in html
    assert html.count("<button") == 2


def test_a_number_inside_a_tag_is_left_where_it_is() -> None:
    """Substituting runs over rendered HTML, so it has to know a tag from the text: a
    number in an attribute is not a citation, and a button written there would break the
    attribute open."""
    html = answer_html('[the note](http://host "see [1] here")', (NOTE,))

    assert 'title="see [1] here"' in html
    assert "<button" not in html


def test_an_image_in_the_answer_fetches_nothing() -> None:
    """Model text shaped by an uploaded document: a markdown image would have the
    reader's browser fetch whatever URL the document asked for, before any click. A
    link is left as a link — that costs a click, and prose has always been able to
    carry one."""
    html = answer_html("![](http://example.invalid/pixel.png) and text", (NOTE,))

    assert "<img" not in html
    assert "src=" not in html
