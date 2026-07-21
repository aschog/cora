from collections.abc import Callable

import pytest

from docchat.chunk import Chunk
from fakes import FakeEmbedder, FakeRetriever


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def retriever() -> FakeRetriever:
    return FakeRetriever()


@pytest.fixture
def make_chunk() -> Callable[..., Chunk]:
    def _make(
        text: str = "chunk",
        source: str = "doc.txt",
        index: int = 0,
        offset: int = 0,
    ) -> Chunk:
        return Chunk(text=text, source=source, index=index, offset=offset)

    return _make
