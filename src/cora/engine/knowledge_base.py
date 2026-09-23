"""The documents side of cora: what is uploaded, and what a search of it returns."""

from dataclasses import dataclass, replace

from cora.domain.chunk import Chunk
from cora.engine.scoping import here
from cora.ports.context_source import Document
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.host import DEFAULT_SCOPE
from cora.ports.retrieval import RetrievedChunk, Retriever


@dataclass
class KnowledgeBase:
    """The documents as one thing: the index, the vectors and the text a citation opens.

    It is the `ContextSource` a search reads from and the `Indexing` a plugin puts a
    document in through, which is why one object holds both sides: a passage is only
    citable if the text it was cut from is still there to open — and it is the one
    place that knows the span in the index and the file the span was measured in are
    two halves of one passage. What a document is cut from, and how, is a plugin's.
    """

    embedder: Embedder
    retriever: Retriever
    documents: Documents

    def add(
        self, scope: str, upload: str, filename: str, text: str, chunks: list[Chunk]
    ) -> bool:
        """Put one upload into one field: its text kept first, then its passages.

        The text goes before the index because a passage in the index is a citation
        waiting to be shown, and a citation onto text nobody kept cannot be opened. A
        failure between the two leaves text and no passage, which is the harmless half.

        Raises:
            AdapterError: A store or the embedder failed.
        """
        if self.retriever.contains(scope, upload):
            # Held already, so nothing is added — but the text is put back where it
            # went missing under cora, because a passage nobody can open is no passage.
            if self.documents.read(scope, upload) is None:
                self.documents.keep(scope, upload, filename, text)
            return False
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.documents.keep(scope, upload, filename, text)
        self.retriever.add(scope, [_span(chunk) for chunk in chunks], vectors, upload)
        return True

    def holds(self, scope: str, upload: str) -> bool:
        """Whether this field already indexed this upload."""
        return self.retriever.contains(scope, upload)

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
        # ponytail: one directory scan per document, so a field costs the square of what
        # it holds — 75 ms at a year of daily logs, under the model round-trip it rides
        # on. A bulk read on `Documents`, one scan for a whole field, if one ever grows
        # past a few hundred.
        return [
            document
            for scope in sorted(here())
            for source in self.retriever.sources(scope)
            for document in self.read(scope, source)
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
