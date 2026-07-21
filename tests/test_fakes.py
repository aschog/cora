from docchat.chunk import Chunk
from fakes import FakeEmbedder, FakeRetriever


def test_fake_embedder_is_deterministic() -> None:
    embedder = FakeEmbedder()

    assert embedder.embed(["hello"]) == embedder.embed(["hello"])


def test_fake_embedder_distinguishes_different_texts() -> None:
    embedder = FakeEmbedder()

    [hello] = embedder.embed(["hello"])
    [world] = embedder.embed(["world"])

    assert hello != world


def test_fake_embedder_produces_fixed_dimension_vectors() -> None:
    embedder = FakeEmbedder(dim=8)

    vectors = embedder.embed(["a", "bb", "ccc"])

    assert len(vectors) == 3
    assert all(len(vector) == 8 for vector in vectors)


def test_fake_embedder_embeds_a_batch_element_wise() -> None:
    embedder = FakeEmbedder()

    batch = embedder.embed(["x", "y"])

    assert batch == [embedder.embed(["x"])[0], embedder.embed(["y"])[0]]


def test_fake_retriever_query_on_empty_store_returns_no_hits() -> None:
    retriever = FakeRetriever()

    assert retriever.query([0.1, 0.2, 0.3], k=3) == []


def test_fake_retriever_ranks_hits_by_cosine_similarity_capped_at_k() -> None:
    embedder = FakeEmbedder()
    retriever = FakeRetriever()
    chunks = [
        Chunk(text="alpha", source="a.txt", index=0, offset=0),
        Chunk(text="beta", source="a.txt", index=1, offset=10),
        Chunk(text="gamma", source="a.txt", index=2, offset=20),
    ]
    retriever.add(chunks, embedder.embed([c.text for c in chunks]), file_hash="h")

    [query_vector] = embedder.embed(["beta"])
    hits = retriever.query(query_vector, k=2)

    assert len(hits) == 2
    assert hits[0].chunk == chunks[1]
    assert hits[0].score >= hits[1].score
