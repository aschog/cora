import hashlib
from dataclasses import dataclass

from docchat.embedding import Embedder
from docchat.ingestion import ingest
from docchat.retrieval import Retriever


@dataclass
class KnowledgeBase:
    embedder: Embedder
    retriever: Retriever

    def add_file(self, data: bytes, filename: str) -> int:
        file_hash = hashlib.sha256(data).hexdigest()
        chunks = ingest(data, filename)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.retriever.add(chunks, vectors, file_hash)
        return len(chunks)
