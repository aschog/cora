import math

import pytest

pytestmark = pytest.mark.integration


def test_embedder_loads_the_model_lazily() -> None:
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()
    assert embedder._model is None

    embedder.embed(["hello"])

    assert embedder._model is not None


def test_embedder_produces_384_dim_unit_vectors() -> None:
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()

    hello, world = embedder.embed(["hello", "world"])

    assert len(hello) == 384
    assert hello != world
    assert math.isclose(math.sqrt(sum(x * x for x in hello)), 1.0, abs_tol=1e-5)

    again = embedder.embed(["hello"])[0]
    assert all(
        math.isclose(a, b, abs_tol=1e-5) for a, b in zip(hello, again, strict=True)
    )


def test_embedder_failure_surfaces_as_embedding_error() -> None:
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
    from cora.domain.errors import EmbeddingError

    embedder = SentenceTransformerEmbedder(model_name="core/not-a-real-model-xyz")

    with pytest.raises(EmbeddingError):
        embedder.embed(["hello"])
