import pytest

from docchat.chunk import Chunk
from fakes import FakeEmbedder, FakeRetriever


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def retriever() -> FakeRetriever:
    return FakeRetriever()


def _chunk(text: str, source: str = "a.txt", index: int = 0, offset: int = 0) -> Chunk:
    return Chunk(text=text, source=source, index=index, offset=offset)


def _add(
    retriever: FakeRetriever,
    embedder: FakeEmbedder,
    chunks: list[Chunk],
    file_hash: str = "h",
) -> None:
    retriever.add(chunks, embedder.embed([c.text for c in chunks]), file_hash=file_hash)


def test_fake_embedder_is_deterministic(embedder: FakeEmbedder) -> None:
    assert embedder.embed(["hello"]) == embedder.embed(["hello"])


def test_fake_embedder_distinguishes_different_texts(embedder: FakeEmbedder) -> None:
    [hello] = embedder.embed(["hello"])
    [world] = embedder.embed(["world"])

    assert hello != world


def test_fake_embedder_produces_fixed_dimension_vectors() -> None:
    embedder = FakeEmbedder(dim=8)

    vectors = embedder.embed(["a", "bb", "ccc"])

    assert len(vectors) == 3
    assert all(len(vector) == 8 for vector in vectors)


def test_fake_embedder_embeds_a_batch_element_wise(embedder: FakeEmbedder) -> None:
    batch = embedder.embed(["x", "y"])

    assert batch == [embedder.embed(["x"])[0], embedder.embed(["y"])[0]]


def test_fake_retriever_query_on_empty_store_returns_no_hits(
    retriever: FakeRetriever,
) -> None:
    assert retriever.query([0.1, 0.2, 0.3], k=3) == []


def test_fake_retriever_ranks_hits_by_cosine_similarity_capped_at_k(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    chunks = [_chunk("alpha"), _chunk("beta"), _chunk("gamma")]
    _add(retriever, embedder, chunks)

    [query_vector] = embedder.embed(["beta"])
    hits = retriever.query(query_vector, k=2)

    assert len(hits) == 2
    assert hits[0].chunk == chunks[1]
    assert hits[0].score >= hits[1].score


def test_fake_retriever_returns_every_record_when_k_exceeds_store(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    chunks = [_chunk("alpha"), _chunk("beta")]
    _add(retriever, embedder, chunks)

    [query_vector] = embedder.embed(["alpha"])
    hits = retriever.query(query_vector, k=10)

    assert len(hits) == 2
    assert hits[0].chunk == chunks[0]


def test_fake_retriever_lists_each_source_once(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    _add(retriever, embedder, [_chunk("a", source="one.txt")], file_hash="h1")
    _add(
        retriever,
        embedder,
        [_chunk("b", source="two.txt"), _chunk("c", source="two.txt", index=1)],
        file_hash="h2",
    )

    assert retriever.sources() == ["one.txt", "two.txt"]


def test_fake_retriever_contains_reports_known_hashes(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    _add(retriever, embedder, [_chunk("a", source="one.txt")], file_hash="h1")

    assert retriever.contains("h1")
    assert not retriever.contains("h2")
