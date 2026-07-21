from collections.abc import Callable
from functools import wraps
from typing import cast

import chromadb
from chromadb.errors import ChromaError

from docchat.chunk import Chunk
from docchat.errors import RetrievalError
from docchat.retrieval import RetrievedChunk


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except ChromaError as error:
            raise RetrievalError() from error

    return wrapper


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
    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        result = self._collection.query(
            query_embeddings=[list(query_vector)],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        documents = (result["documents"] or [[]])[0]
        metadatas = (result["metadatas"] or [[]])[0]
        distances = (result["distances"] or [[]])[0]
        return [
            RetrievedChunk(
                chunk=Chunk(
                    text=str(document),
                    source=cast(str, metadata["source"]),
                    index=cast(int, metadata["index"]),
                    offset=cast(int, metadata["offset"]),
                ),
                score=1.0 - distance,
            )
            for document, metadata, distance in zip(
                documents, metadatas, distances, strict=True
            )
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
