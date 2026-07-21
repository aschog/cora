from docchat.ingestion import ingest
from docchat.knowledge_base import KnowledgeBase
from fakes import FakeEmbedder, FakeRetriever


def test_add_file_embeds_and_stores_one_record_per_chunk() -> None:
    data = ("lorem ipsum dolor sit amet " * 100).encode()
    embedder = FakeEmbedder()
    retriever = FakeRetriever()
    kb = KnowledgeBase(embedder=embedder, retriever=retriever)

    added = kb.add_file(data, "doc.txt")

    assert added == len(ingest(data, "doc.txt"))
    assert added >= 2
    assert retriever.sources() == ["doc.txt"]

    stored = retriever.query(embedder.embed(["probe"])[0], k=added + 5)
    assert len(stored) == added
    assert all(hit.chunk.source == "doc.txt" for hit in stored)
