from collections.abc import Callable, Mapping
from functools import wraps
from typing import cast

import chromadb
from chromadb.errors import ChromaError

from cora.core.chunk import Chunk
from cora.core.errors import RetrievalError
from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.retrieval import RetrievedChunk


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except ChromaError as error:
            raise RetrievalError() from error

    return wrapper


def _to_chunk(document: object, metadata: Mapping[str, object]) -> Chunk:
    return Chunk(
        text=str(document),
        source=cast(str, metadata["source"]),
        index=cast(int, metadata["index"]),
        offset=cast(int, metadata["offset"]),
    )


class ChromaRetriever:
    @_translate_errors
    def __init__(self, path: str, collection: str) -> None:
        client = chromadb.PersistentClient(path=path)
        self._collection = client.get_or_create_collection(
            name=collection, configuration={"hnsw": {"space": "cosine"}}
        )

    @_translate_errors
    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        self._collection.add(
            ids=[f"{file_hash}:{chunk.index}" for chunk in chunks],
            embeddings=[list(vector) for vector in vectors],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "source": chunk.source,
                    "index": chunk.index,
                    "offset": chunk.offset,
                    "file_hash": file_hash,
                }
                for chunk in chunks
            ],
        )

    @_translate_errors
    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        where = (
            {metadata_filter.field: metadata_filter.value}
            if metadata_filter is not None
            else None
        )
        result = self._collection.query(
            query_embeddings=[list(query_vector)],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        documents = (result["documents"] or [[]])[0]
        metadatas = (result["metadatas"] or [[]])[0]
        distances = (result["distances"] or [[]])[0]
        return [
            RetrievedChunk(chunk=_to_chunk(document, metadata), score=1.0 - distance)
            for document, metadata, distance in zip(
                documents, metadatas, distances, strict=True
            )
        ]

    @_translate_errors
    def all_chunks(self) -> list[Chunk]:
        result = self._collection.get(include=["documents", "metadatas"])
        documents = result["documents"] or []
        metadatas = result["metadatas"] or []
        return [
            _to_chunk(document, metadata)
            for document, metadata in zip(documents, metadatas, strict=True)
        ]

    @_translate_errors
    def sources(self) -> list[str]:
        metadatas = self._collection.get(include=["metadatas"])["metadatas"] or []
        return list(
            dict.fromkeys(cast(str, metadata["source"]) for metadata in metadatas)
        )

    @_translate_errors
    def contains(self, file_hash: str) -> bool:
        found = self._collection.get(where={"file_hash": file_hash}, limit=1)
        return len(found["ids"]) > 0
