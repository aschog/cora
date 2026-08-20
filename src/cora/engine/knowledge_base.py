"""The documents side of cora: what is uploaded, and what a search of it returns."""

import hashlib
from dataclasses import dataclass

from cora.engine.ingestion import ingest
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.loading import Loaders
from cora.ports.retrieval import RetrievedChunk, Retriever


@dataclass
class KnowledgeBase:
    """The uploads, as one thing: the index, the vectors and the text behind a citation.

    It is also the `ContextSource` the search tool reads from, which is why one object
    holds both sides: a passage is only citable if the text it was cut from is still
    there to open.
    """

    embedder: Embedder
    retriever: Retriever
    loaders: Loaders
    documents: Documents

    def add_file(self, data: bytes, filename: str) -> int:
        """Take an upload into the knowledge base, and say how many chunks it added.

        Zero means the bytes were already indexed — the same file uploaded twice costs
        nothing and adds nothing. The text is kept alongside the vectors because a
        citation is a span of it: a passage in the index is a citation waiting to be
        shown, so it is kept *before* the index will hand that passage out. A failure
        there costs the upload, which the user is told about; the other order leaves a
        document that is searchable, citable and unopenable. Ingestion raises before
        either write, so a document that cannot be read still leaves nothing behind.

        Raises:
            IngestionError: The document was refused. Nothing was written.
            AdapterError: A store or the embedder failed.
        """
        file_hash = hashlib.sha256(data).hexdigest()
        if self.retriever.contains(file_hash):
            self._repair(data, filename, file_hash)
            return 0
        text, chunks = ingest(data, filename, self.loaders)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.documents.keep(file_hash, text)
        self.retriever.add(chunks, vectors, file_hash)
        return len(chunks)

    def _repair(self, data: bytes, filename: str, file_hash: str) -> None:
        """Keep the text of an upload that was indexed before any text was kept.

        An index that holds passages whose text was never kept hands out citations that
        open onto nothing, and `contains` would leave it that way for good. Uploading
        the same file again is the repair, and it costs the parse rather than the
        embeddings.
        """
        if self.documents.read(file_hash) is not None:
            return
        text, _ = ingest(data, filename, self.loaders)
        self.documents.keep(file_hash, text)

    def text(self, upload: str) -> str | None:
        """The text one upload arrived as, or nothing if it was never kept.

        A passage carries the upload it was cut from, so what comes back is the text its
        offsets were measured in — not whatever now goes by the same filename.
        """
        return self.documents.read(upload)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        """The `k` passages closest to a question, closest first.

        The query goes through the same embedder the chunks did, which is the only way
        the distances mean anything.
        """
        [query_vector] = self.embedder.embed([query])
        return self.retriever.query(query_vector, k)

    def list_sources(self) -> list[str]:
        """Every document the index holds a passage from, by its uploaded name."""
        return self.retriever.sources()
