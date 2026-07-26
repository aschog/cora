from cora.app.ui.formatting import numbered_sources


def test_numbered_sources_renders_bracketed_numbers_in_order() -> None:
    assert numbered_sources(("a.pdf", "b.md")) == ["[1] a.pdf", "[2] b.md"]


def test_numbered_sources_of_nothing_is_empty() -> None:
    assert numbered_sources(()) == []
