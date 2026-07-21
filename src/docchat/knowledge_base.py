import hashlib
from dataclasses import dataclass

from docchat.embedding import Embedder
from docchat.ingestion import ingest
from docchat.retrieval import RetrievedChunk, Retriever


@dataclass
class KnowledgeBase:
    embedder: Embedder
    retriever: Retriever

    def add_file(self, data: bytes, filename: str) -> int:
        file_hash = hashlib.sha256(data).hexdigest()
        if self.retriever.contains(file_hash):
            return 0
        chunks = ingest(data, filename)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.retriever.add(chunks, vectors, file_hash)
        return len(chunks)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        [query_vector] = self.embedder.embed([query])
        return self.retriever.query(query_vector, k)

    def list_sources(self) -> list[str]:
        return self.retriever.sources()
