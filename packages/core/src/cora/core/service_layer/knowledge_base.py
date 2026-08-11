import hashlib
from dataclasses import dataclass
from typing import Protocol

from cora.core.domain.chunk import Chunk
from cora.core.domain.metadata_filter import MetadataFilter
from cora.core.ports.embedding import Embedder
from cora.core.ports.loading import Loaders
from cora.core.ports.retrieval import RetrievedChunk, Retriever
from cora.core.service_layer.ingestion import ingest


class KeywordIndex(Protocol):
    def add(self, chunks: list[Chunk]) -> None: ...


@dataclass
class KnowledgeBase:
    embedder: Embedder
    retriever: Retriever
    loaders: Loaders
    keyword_index: KeywordIndex | None = None

    def add_file(self, data: bytes, filename: str) -> int:
        file_hash = hashlib.sha256(data).hexdigest()
        if self.retriever.contains(file_hash):
            return 0
        chunks = ingest(data, filename, self.loaders)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.retriever.add(chunks, vectors, file_hash)
        if self.keyword_index is not None:
            self.keyword_index.add(chunks)
        return len(chunks)

    def search(
        self, query: str, k: int, metadata_filter: MetadataFilter | None = None
    ) -> list[RetrievedChunk]:
        [query_vector] = self.embedder.embed([query])
        return self.retriever.query(query_vector, k, metadata_filter)

    def list_sources(self) -> list[str]:
        return self.retriever.sources()
