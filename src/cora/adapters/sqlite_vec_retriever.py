import pathlib
import sqlite3
from collections.abc import Callable
from functools import wraps

import sqlite_vec

from cora.domain.chunk import Chunk
from cora.domain.errors import RetrievalError
from cora.ports.retrieval import RetrievedChunk

LOCAL = "local"
"""The one user a deployment has. The column is here so a second one costs a value
rather than an alter and a backfill."""

PASSAGES = (
    "create table if not exists passages ("
    "id integer primary key autoincrement, "
    "user text not null, scope text not null, source text not null, "
    "position integer not null, start integer not null, length integer not null, "
    "file_hash text not null)"
)
VECTORS = (
    "create virtual table if not exists vectors using vec0("
    "id integer primary key, embedding float[{width}] distance_metric=cosine, "
    "scope text partition key)"
)


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except sqlite3.Error as error:
            raise RetrievalError() from error

    return wrapper


class SqliteVecRetriever:
    """The spans in a table, the vectors in a `vec0` table beside it, in one file.

    A field is `vec0`'s partition key rather than a clause, so a field's vectors sit
    apart and a leak is not one missing `where` away. Only searching touches the vector
    table: listing and forgetting are plain SQL over the spans.

    The vector table is created by the first write, at the width of the vector it is
    handed, because how wide an embedding is belongs to the embedder and not here.
    """

    def __init__(self, connection: sqlite3.Connection, user: str = LOCAL) -> None:
        self._connection = connection
        self._user = user

    @classmethod
    @_translate_errors
    def at(cls, path: str, user: str = LOCAL) -> "SqliteVecRetriever":
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None
        )
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        connection.execute(PASSAGES)
        return cls(connection, user)

    @_translate_errors
    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        if not chunks:
            return
        self._connection.execute(VECTORS.format(width=len(vectors[0])))
        self.forget(scope, file_hash)
        for chunk, vector in zip(chunks, vectors, strict=True):
            cursor = self._connection.execute(
                "insert into passages "
                "(user, scope, source, position, start, length, file_hash) "
                "values (?, ?, ?, ?, ?, ?, ?)",
                (
                    self._user,
                    scope,
                    chunk.source,
                    chunk.index,
                    chunk.offset,
                    chunk.length,
                    file_hash,
                ),
            )
            self._connection.execute(
                "insert into vectors (id, embedding, scope) values (?, ?, ?)",
                (
                    cursor.lastrowid,
                    sqlite_vec.serialize_float32(vector),
                    scope,
                ),
            )

    @_translate_errors
    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        if not self._indexed():
            return []
        nearest = self._connection.execute(
            "select id, distance from vectors "
            "where embedding match ? and k = ? and scope = ? order by distance",
            (sqlite_vec.serialize_float32(query_vector), k, scope),
        ).fetchall()
        return [
            RetrievedChunk(chunk=self._chunk(row_id), score=1.0 - distance)
            for row_id, distance in nearest
        ]

    @_translate_errors
    def sources(self, scope: str) -> list[str]:
        rows = self._connection.execute(
            "select source from passages where user = ? and scope = ? order by id",
            (self._user, scope),
        ).fetchall()
        return list(dict.fromkeys(row[0] for row in rows))

    @_translate_errors
    def forget(self, scope: str, file_hash: str) -> None:
        going = self._connection.execute(
            "select id from passages where user = ? and scope = ? and file_hash = ?",
            (self._user, scope, file_hash),
        ).fetchall()
        if not going:
            return
        marks = ", ".join("?" * len(going))
        ids = [row[0] for row in going]
        if self._indexed():
            self._connection.execute(
                f"delete from vectors where scope = ? and id in ({marks})",
                (scope, *ids),
            )
        self._connection.execute(f"delete from passages where id in ({marks})", ids)

    @_translate_errors
    def uploads(self, scope: str, source: str) -> list[str]:
        rows = self._connection.execute(
            "select file_hash from passages "
            "where user = ? and scope = ? and source = ? order by id",
            (self._user, scope, source),
        ).fetchall()
        return list(dict.fromkeys(row[0] for row in rows))

    @_translate_errors
    def contains(self, scope: str, file_hash: str) -> bool:
        found = self._connection.execute(
            "select 1 from passages "
            "where user = ? and scope = ? and file_hash = ? limit 1",
            (self._user, scope, file_hash),
        ).fetchone()
        return found is not None

    def close(self) -> None:
        self._connection.close()

    def _indexed(self) -> bool:
        """Whether anything has been written yet: the vector table is the first write's
        doing, and a search before it is an empty field rather than a missing table."""
        return (
            self._connection.execute(
                "select 1 from sqlite_master where name = 'vectors'"
            ).fetchone()
            is not None
        )

    def _chunk(self, row_id: int) -> Chunk:
        source, position, start, length, file_hash, scope = self._connection.execute(
            "select source, position, start, length, file_hash, scope "
            "from passages where id = ?",
            (row_id,),
        ).fetchone()
        return Chunk(
            text="",
            source=source,
            index=position,
            offset=start,
            length=length,
            upload=file_hash,
            scope=scope,
        )
