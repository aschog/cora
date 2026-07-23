from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from core.chunk import Chunk
from core.knowledge_base import KnowledgeBase
from fakes import FakeEmbedder, FakeRetriever

if TYPE_CHECKING:
    from core.chroma_retriever import ChromaRetriever


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
def make_chroma(tmp_path: Path) -> "Callable[[], ChromaRetriever]":
    def _make() -> "ChromaRetriever":
        from core.chroma_retriever import ChromaRetriever

        return ChromaRetriever(path=str(tmp_path), collection="documents")

    return _make


@pytest.fixture
def chroma_retriever(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> "ChromaRetriever":
    return make_chroma()
