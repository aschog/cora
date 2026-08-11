from __future__ import annotations

from typing import TYPE_CHECKING, cast

from cora.core.domain.errors import EmbeddingError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            vectors = self._load().encode(texts, normalize_embeddings=True)
            return cast("list[list[float]]", vectors.tolist())
        except Exception as error:
            raise EmbeddingError() from error

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model
