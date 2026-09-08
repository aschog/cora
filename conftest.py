import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cora.domain.chunk import Chunk
from cora.engine.knowledge_base import KnowledgeBase
from fakes import TEXT_LOADERS, FakeDocuments, FakeEmbedder, FakeRetriever

if TYPE_CHECKING:
    from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever


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
def documents() -> FakeDocuments:
    return FakeDocuments()


@pytest.fixture
def kb(
    embedder: FakeEmbedder, retriever: FakeRetriever, documents: FakeDocuments
) -> KnowledgeBase:
    return KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=documents,
    )


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
def make_index(tmp_path: Path) -> "Callable[[], SqliteVecRetriever]":
    def _make() -> "SqliteVecRetriever":
        from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever

        return SqliteVecRetriever.at(str(tmp_path / "index.sqlite"))

    return _make


@pytest.fixture
def index(
    make_index: "Callable[[], SqliteVecRetriever]",
) -> "SqliteVecRetriever":
    return make_index()
