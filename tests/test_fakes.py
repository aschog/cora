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
