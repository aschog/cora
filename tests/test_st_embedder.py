import pytest

pytestmark = pytest.mark.integration


def test_embedder_loads_the_model_lazily() -> None:
    from docchat.sentence_transformer_embedder import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()
    assert embedder._model is None

    embedder.embed(["hello"])

    assert embedder._model is not None
