from core.knowledge_base import KnowledgeBase
from plugins.fitness.seed_docs import SEED_DOCS


def test_seed_docs_are_nonempty_markdown_byte_pairs() -> None:
    assert SEED_DOCS

    for filename, data in SEED_DOCS:
        assert filename.endswith(".md")
        assert isinstance(data, bytes)
        assert data.decode("utf-8").strip()


def test_every_seed_doc_ingests_into_the_knowledge_base(kb: KnowledgeBase) -> None:
    for filename, data in SEED_DOCS:
        assert kb.add_file(data=data, filename=filename) >= 1
