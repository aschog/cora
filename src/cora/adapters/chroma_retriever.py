from collections.abc import Callable, Mapping
from functools import wraps
from typing import cast

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.errors import ChromaError

from cora.domain.chunk import Chunk
from cora.domain.errors import RetrievalError
from cora.ports.retrieval import RetrievedChunk


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except ChromaError as error:
            raise RetrievalError() from error

    return wrapper


def _to_chunk(scope: str, metadata: Mapping[str, object]) -> Chunk:
    """The span the index kept, with no words in it: the file holds those."""
    return Chunk(
        text="",
        source=cast(str, metadata["source"]),
        index=cast(int, metadata["index"]),
        offset=cast(int, metadata["offset"]),
        length=cast(int, metadata["length"]),
        upload=cast(str, metadata["file_hash"]),
        scope=scope,
    )


class ChromaRetriever:
    """One collection per field, named for it under a shared prefix.

    A field is a collection rather than a filter, so a passage of one is unreachable
    from another rather than merely left out of a result — and an empty field is an
    empty collection, which is the honest answer to searching one nothing was uploaded
    to.
    """

    @_translate_errors
    def __init__(self, path: str, collection: str) -> None:
        self._client = chromadb.PersistentClient(path=path)
        self._prefix = collection
        self._collections: dict[str, Collection] = {}

    def _of(self, scope: str) -> Collection:
        if scope not in self._collections:
            self._collections[scope] = self._client.get_or_create_collection(
                name=f"{self._prefix}-{scope}",
                configuration={"hnsw": {"space": "cosine"}},
            )
        return self._collections[scope]

    @_translate_errors
    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        self._of(scope).add(
            ids=[f"{file_hash}:{chunk.index}" for chunk in chunks],
            embeddings=[list(vector) for vector in vectors],
            metadatas=[
                {
                    "source": chunk.source,
                    "index": chunk.index,
                    "offset": chunk.offset,
                    "length": chunk.length,
                    "file_hash": file_hash,
                }
                for chunk in chunks
            ],
        )

    @_translate_errors
    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        result = self._of(scope).query(
            query_embeddings=[list(query_vector)],
            n_results=k,
            include=["metadatas", "distances"],
        )
        metadatas = (result["metadatas"] or [[]])[0]
        distances = (result["distances"] or [[]])[0]
        return [
            RetrievedChunk(chunk=_to_chunk(scope, metadata), score=1.0 - distance)
            for metadata, distance in zip(metadatas, distances, strict=True)
        ]

    @_translate_errors
    def sources(self, scope: str) -> list[str]:
        metadatas = self._of(scope).get(include=["metadatas"])["metadatas"] or []
        return list(
            dict.fromkeys(cast(str, metadata["source"]) for metadata in metadatas)
        )

    @_translate_errors
    def contains(self, scope: str, file_hash: str) -> bool:
        found = self._of(scope).get(where={"file_hash": file_hash}, limit=1)
        return len(found["ids"]) > 0
