import uuid
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from docchat.chunk import Chunk
from docchat.knowledge_base import KnowledgeBase
from fakes import FakeEmbedder, FakeRetriever

if TYPE_CHECKING:
    from docchat.chroma_retriever import ChromaRetriever


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def retriever() -> FakeRetriever:
    return FakeRetriever()


@pytest.fixture
def kb(embedder: FakeEmbedder, retriever: FakeRetriever) -> KnowledgeBase:
    return KnowledgeBase(embedder=embedder, retriever=retriever)


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


@pytest.fixture
def chroma_retriever(tmp_path: Path) -> "ChromaRetriever":
    from docchat.chroma_retriever import ChromaRetriever

    return ChromaRetriever(path=str(tmp_path), collection=f"kb-{uuid.uuid4().hex}")
