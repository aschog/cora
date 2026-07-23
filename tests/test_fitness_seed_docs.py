from docchat_plugins.fitness.seed_docs import SEED_DOCS


def test_seed_docs_are_nonempty_markdown_byte_pairs() -> None:
    assert SEED_DOCS

    for filename, data in SEED_DOCS:
        assert filename.endswith(".md")
        assert isinstance(data, bytes)
        assert data.decode("utf-8").strip()
