import pathlib
import re

import pytest

TAGS = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")
# Every token of a rendered signature is its own element, so stripping tags leaves
# `list [ RetrievedChunk ]` where the source says `list[RetrievedChunk]`.
BRACKETS = re.compile(r"\s*([\[\]()])\s*")
# The page also carries every definition's source in a collapsed block. Asserting over
# that would pass on any rendering at all, so it comes out before anything is read.
SOURCE = re.compile(r"<details\b.*?</details>", re.DOTALL)


def _markup(built: pathlib.Path, dotted: str) -> str:
    page = built.joinpath("api", *dotted.split(".")) / "index.html"
    return SOURCE.sub(" ", page.read_text())


def _text(built: pathlib.Path, dotted: str) -> str:
    plain = SPACE.sub(" ", TAGS.sub(" ", _markup(built, dotted)))
    return BRACKETS.sub(r"\1", plain)


@pytest.mark.integration
def test_a_frozen_dataclass_shows_its_fields_with_annotations(
    built: pathlib.Path,
) -> None:
    plugin = _text(built, "cora.ports.plugin")
    assert "ToolResult" in plugin
    assert "error" in plugin
    assert "str | None" in plugin


@pytest.mark.integration
def test_a_dataclass_shows_its_annotated_fields_beside_its_prose(
    built: pathlib.Path,
) -> None:
    result = _text(built, "cora.domain.chat_result")
    assert "ChatResult dataclass" in result
    # The annotated field, not the bare name: every name is also a contents entry, so a
    # name-only assertion holds whatever the page renders.
    for field in ("answer : str", "citations : tuple[Citation , ...]=()"):
        assert field in result, field


@pytest.mark.integration
def test_a_protocols_methods_show_their_signatures(built: pathlib.Path) -> None:
    retrieval = _text(built, "cora.ports.retrieval")
    assert "query" in retrieval
    assert "list[RetrievedChunk]" in retrieval


@pytest.mark.integration
def test_an_error_subclass_shows_what_it_inherits(built: pathlib.Path) -> None:
    errors = _text(built, "cora.domain.errors")
    # The pair, not the two names: both classes are defined in this module, so each is a
    # heading and a contents entry however the bases render.
    assert "UnsupportedFileTypeError Bases: IngestionError" in errors
    assert "IngestionError Bases: CoreError" in errors


@pytest.mark.integration
def test_a_hierarchy_reads_in_source_order(built: pathlib.Path) -> None:
    errors = _text(built, "cora.domain.errors")
    # These three invert under alphabetical ordering, which is the point — and `Bases:`
    # only follows a rendered class, so this reads the article, not the contents list.
    inverting = (
        r"(UnsupportedFileTypeError|FileTooLargeError|EmptyDocumentError) Bases:"
    )
    found = re.findall(inverting, errors)
    assert found == [
        "UnsupportedFileTypeError",
        "FileTooLargeError",
        "EmptyDocumentError",
    ]


@pytest.mark.integration
def test_a_raises_section_renders_as_a_section(built: pathlib.Path) -> None:
    """The one thing no annotation carries has to read as structure: a titled section
    over a table, not the docstring's own indentation left as prose."""
    assert '<span class="doc-section-title">Raises:</span>' in _markup(
        built, "cora.ports.embedding"
    )
    embedding = _text(built, "cora.ports.embedding")

    assert "Raises: Type Description EmbeddingError" in embedding


@pytest.mark.integration
def test_an_undocumented_parameter_still_shows_its_annotation(
    built: pathlib.Path,
) -> None:
    """`ingest` documents three of its four, because `data: bytes` is what an `Args:`
    entry could only restate. The one left out is still on the page — from the
    signature, which is where a type belongs."""
    ingestion = _text(built, "cora.engine.ingestion")
    parameters = ingestion.split("Parameters:")[1].split("Raises:")[0]

    assert "ingest(data : bytes ," in ingestion
    for documented in ("filename str", "loaders Loaders", "max_bytes int"):
        assert documented in parameters, documented
    assert "data" not in parameters


@pytest.mark.integration
def test_a_protocols_page_carries_the_ordering_it_guarantees(
    built: pathlib.Path,
) -> None:
    """An implementer reads the contract here: `ty` checks the signatures and nothing
    else states the order the results come back in."""
    conversations = _text(built, "cora.ports.conversations")

    assert "oldest first" in conversations
    assert "newest first" in conversations
