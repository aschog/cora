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


def _text(built: pathlib.Path, dotted: str) -> str:
    page = built.joinpath("api", *dotted.split(".")) / "index.html"
    rendered = SOURCE.sub(" ", page.read_text())
    plain = SPACE.sub(" ", TAGS.sub(" ", rendered))
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
def test_a_class_with_no_docstring_still_shows_its_annotated_fields(
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
