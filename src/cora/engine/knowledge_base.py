import hashlib
from dataclasses import dataclass

from cora.engine.ingestion import ingest
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.loading import Loaders
from cora.ports.retrieval import RetrievedChunk, Retriever


@dataclass
class KnowledgeBase:
    embedder: Embedder
    retriever: Retriever
    loaders: Loaders
    documents: Documents

    def add_file(self, data: bytes, filename: str) -> int:
        """The text is kept alongside the vectors because a citation is a span of it:
        indexing a document the pane could not then open would put a number on screen
        with nothing behind it. Kept after the index accepts the chunks, so a document
        that failed to ingest leaves nothing."""
        file_hash = hashlib.sha256(data).hexdigest()
        if self.retriever.contains(file_hash):
            return 0
        text, chunks = ingest(data, filename, self.loaders)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.retriever.add(chunks, vectors, file_hash)
        self.documents.keep(filename, text)
        return len(chunks)

    def text(self, name: str) -> str | None:
        return self.documents.read(name)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        [query_vector] = self.embedder.embed([query])
        return self.retriever.query(query_vector, k)

    def list_sources(self) -> list[str]:
        return self.retriever.sources()
