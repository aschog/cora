import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cora.core.service_layer.knowledge_base import KnowledgeBase
from cora.domain.chunk import Chunk
from fakes import TEXT_LOADERS, FakeEmbedder, FakeRetriever

if TYPE_CHECKING:
    from cora.adapters.chroma_retriever import ChromaRetriever


@pytest.fixture
def clean_cora_logger() -> Iterator[logging.Logger]:
    logger = logging.getLogger("cora")
    level, handlers = logger.level, list(logger.handlers)
    logger.setLevel(logging.NOTSET)
    logger.handlers = []
    yield logger
    for handler in logger.handlers:
        handler.close()
    logger.setLevel(level)
    logger.handlers = handlers


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def retriever() -> FakeRetriever:
    return FakeRetriever()


@pytest.fixture
def kb(embedder: FakeEmbedder, retriever: FakeRetriever) -> KnowledgeBase:
    return KnowledgeBase(embedder=embedder, retriever=retriever, loaders=TEXT_LOADERS)


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
        from cora.adapters.chroma_retriever import ChromaRetriever

        return ChromaRetriever(path=str(tmp_path), collection="documents")

    return _make


@pytest.fixture
def chroma_retriever(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> "ChromaRetriever":
    return make_chroma()
