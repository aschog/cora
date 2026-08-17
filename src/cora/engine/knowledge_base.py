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
        a passage in the index is a citation waiting to be shown, so it is kept *before*
        the index will hand that passage out. A failure there costs the upload, which
        the user is told about; the other order leaves a document that is searchable,
        citable and unopenable, and says "already in your knowledge base" on the retry.
        Ingestion raises before either write, so a document that cannot be read still
        leaves nothing behind."""
        file_hash = hashlib.sha256(data).hexdigest()
        if self.retriever.contains(file_hash):
            return 0
        text, chunks = ingest(data, filename, self.loaders)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.documents.keep(file_hash, text)
        self.retriever.add(chunks, vectors, file_hash)
        return len(chunks)

    def text(self, upload: str) -> str | None:
        """The text one upload arrived as. A passage carries the upload it was cut
        from, so what comes back is the text its offsets were measured in — not
        whatever now goes by the same filename."""
        return self.documents.read(upload)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        [query_vector] = self.embedder.embed([query])
        return self.retriever.query(query_vector, k)

    def list_sources(self) -> list[str]:
        return self.retriever.sources()
