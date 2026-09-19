"""The documents side of cora: what is uploaded, and what a search of it returns."""

import hashlib
from dataclasses import dataclass, replace

from cora.domain.chunk import Chunk
from cora.engine.ingestion import ingest
from cora.engine.scoping import here
from cora.ports.context_source import Document
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.host import DEFAULT_SCOPE
from cora.ports.loading import Loaders
from cora.ports.retrieval import RetrievedChunk, Retriever


@dataclass
class KnowledgeBase:
    """The uploads, as one thing: the index, the vectors and the text behind a citation.

    It is also the `ContextSource` the search tool reads from, which is why one object
    holds both sides: a passage is only citable if the text it was cut from is still
    there to open — and it is the one place that knows the span in the index and the
    file the span was measured in are two halves of one passage.
    """

    embedder: Embedder
    retriever: Retriever
    loaders: Loaders
    documents: Documents

    def add_file(self, data: bytes, filename: str, scope: str = DEFAULT_SCOPE) -> int:
        """Take an upload into one field, and say how many chunks it added.

        Zero means the bytes were already in that field — the same file uploaded twice
        costs nothing and adds nothing, while the same file added to a second field is
        new there, because a field is meant to be self-contained. The text is kept
        alongside the vectors because a citation is a span of it: a passage in the index
        is a citation waiting to be shown, so it is kept *before* the index will hand
        that passage out. A failure there costs the upload, which the user is told
        about; the other order leaves a document that is searchable, citable and
        unopenable. Ingestion raises before either write, so a document that cannot be
        read still leaves nothing behind.

        Args:
            scope: The field it lands in, whose directory the text is kept under and
                whose index it goes into. It defaults where `search` takes none at all,
                because an upload happens outside a turn: there is no field to inherit,
                and the default one is a field like any other to land in.

        Raises:
            IngestionError: The document was refused. Nothing was written.
            AdapterError: A store or the embedder failed.
        """
        file_hash = hashlib.sha256(data).hexdigest()
        if self.retriever.contains(scope, file_hash):
            self._repair(data, filename, file_hash, scope)
            return 0
        text, chunks = ingest(data, filename, self.loaders)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.documents.keep(scope, file_hash, filename, text)
        self.retriever.add(
            scope, [_span(chunk) for chunk in chunks], vectors, file_hash
        )
        return len(chunks)

    def _repair(self, data: bytes, filename: str, file_hash: str, scope: str) -> None:
        if self.documents.read(scope, file_hash) is not None:
            return
        text, _ = ingest(data, filename, self.loaders)
        self.documents.keep(scope, file_hash, filename, text)

    def forget(self, scope: str, name: str) -> None:
        """Delete a document from one field: its passages, and the file behind them.

        The name is what the field lists, and one name may be several uploads — the
        bytes name an upload, so the same filename twice is two documents under one
        entry, and all of them go.

        Each upload's passages leave the index before its file leaves the directory,
        which is `add_file`'s order run backwards. The other order leaves a document
        still listed whose passages every search drops.

        A field owns its documents, so one ingested into another is left where it is.

        Raises:
            RetrievalError: The index could not be read or written.
            DocumentStoreError: A file could not be deleted.
        """
        for upload in self.retriever.uploads(scope, name):
            self.retriever.forget(scope, upload)
            self.documents.forget(scope, upload)

    def text(self, scope: str, upload: str) -> str | None:
        """The text one upload arrived as, or nothing if it was never kept.

        A passage carries the upload it was cut from and the field it was kept under, so
        what comes back is the text its offsets were measured in — not whatever now goes
        by the same filename, and not another field's document of that name.
        """
        return self.documents.read(scope, upload)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        """The `k` passages closest to a question in the fields the turn is running in.

        The query goes through the same embedder the chunks did, which is the only way
        the distances mean anything. Which fields is not asked for: it is what the work
        happening now is running in, so a plugin's search and cora's own read the same
        one without either being handed it.

        The cut to `k` comes after a passage whose file is gone has been left out,
        which is what keeps the merge across two fields from spending its places on
        passages that are then dropped. The index is asked for `k` per field, so a field
        whose files have been deleted under cora still answers with fewer.
        """
        [query_vector] = self.embedder.embed([query])
        found = [
            hit
            for scope in sorted(here())
            for hit in self.retriever.query(scope, query_vector, k)
        ]
        found.sort(key=lambda hit: hit.score, reverse=True)
        return self._written(found)[:k]

    def list_sources(self, scope: str = DEFAULT_SCOPE) -> list[str]:
        """Every document one field holds a passage from, by its uploaded name."""
        return self.retriever.sources(scope)

    def read(self, scope: str, name: str) -> list[Document]:
        """Every upload one field holds under a name, each with its text, oldest first.

        The name is what the field lists, and one name may be several uploads — each
        comes back as its own document, as `all` hands them and as `forget` takes them.
        One whose text is gone is left out, and a name nothing was uploaded under reads
        as nothing.
        """
        return [
            Document(name=name, text=text, scope=scope)
            for upload in self.retriever.uploads(scope, name)
            if (text := self.documents.read(scope, upload)) is not None
        ]

    def all(self) -> list[Document]:
        """Every document in the fields the turn is running in, by name and by text.

        Read as `search` reads: the fields are what the work happening now runs in, and
        a document whose file is gone under cora is left out rather than handed back
        empty. The names come in the order first uploaded, the uploads of one name
        together and oldest first, which is the order the index lists them in.
        """
        return [
            Document(name=source, text=text, scope=scope)
            for scope in sorted(here())
            for source in self.retriever.sources(scope)
            for upload in self.retriever.uploads(scope, source)
            if (text := self.documents.read(scope, upload)) is not None
        ]

    def _written(self, hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
        written = []
        for hit in hits:
            text = self.documents.read(hit.chunk.scope, hit.chunk.upload)
            if text is None:
                continue
            cut = text[hit.chunk.offset : hit.chunk.offset + hit.chunk.length]
            if not cut:
                continue
            written.append(replace(hit, chunk=replace(hit.chunk, text=cut)))
        return written


def _span(chunk: Chunk) -> Chunk:
    return replace(chunk, text="")
