import sqlite3
from collections.abc import Callable
from functools import wraps

import sqlite_vec

from cora.adapters.sqlite_store import connect
from cora.domain.chunk import Chunk
from cora.domain.errors import RetrievalError
from cora.ports.retrieval import RetrievedChunk

LOCAL = "local"
"""The one user a deployment has. The column is here so a second one costs a value
rather than an alter and a backfill."""

PASSAGES = (
    "create table if not exists cora_passages ("
    "id integer primary key autoincrement, "
    "user text not null, scope text not null, source text not null, "
    "position integer not null, start integer not null, length integer not null, "
    "file_hash text not null)"
)
VECTORS = (
    "create virtual table if not exists cora_vectors using vec0("
    "id integer primary key, embedding float[{width}] distance_metric=cosine, "
    "scope text partition key)"
)
"""The width is the first vector's, and the file keeps it: an embedder of another width
cannot be indexed into a store already holding one.

ponytail: fixed at the first write, and the way out is deleting the store and uploading
again — which is what a changed embedder needs anyway, its old vectors meaning nothing.
"""


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except (sqlite3.Error, OSError, AttributeError) as error:
            # `OSError` is the directory the store could not be made in, and
            # `AttributeError` the build without extension loading: CPython compiled
            # with `SQLITE_OMIT_LOAD_EXTENSION` has no `enable_load_extension` at all.
            raise RetrievalError() from error

    return wrapper


class SqliteVecRetriever:
    """The spans in a table, the vectors in a `vec0` table beside it, in one file.

    A field is `vec0`'s partition key rather than a clause, so a field's vectors sit
    apart and a leak is not one missing `where` away. Only searching touches the vector
    table, and it joins back to the spans — listing and forgetting are plain SQL.

    The vector table is created by the first write, at the width of the vector it is
    handed, because how wide an embedding is belongs to the embedder and not here.
    """

    def __init__(self, connection: sqlite3.Connection, user: str = LOCAL) -> None:
        self._connection = connection
        self._user = user

    @classmethod
    @_translate_errors
    def at(cls, path: str, user: str = LOCAL) -> "SqliteVecRetriever":
        connection = connect(path)
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
        """One transaction, because the engine gates a re-upload on `contains`: a span
        written without its vector is a document the rail lists, a search cannot find,
        and uploading again will not repair."""
        if not chunks:
            return
        self._connection.execute(VECTORS.format(width=len(vectors[0])))
        with self._transaction():
            self._drop(scope, file_hash)
            self._connection.executemany(
                "insert into cora_passages "
                "(user, scope, source, position, start, length, file_hash) "
                "values (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        self._user,
                        scope,
                        chunk.source,
                        chunk.index,
                        chunk.offset,
                        chunk.length,
                        file_hash,
                    )
                    for chunk in chunks
                ],
            )
            self._connection.executemany(
                "insert into cora_vectors (id, embedding, scope) values (?, ?, ?)",
                [
                    (row_id, sqlite_vec.serialize_float32(vector), scope)
                    for row_id, vector in zip(
                        self._written(scope, file_hash), vectors, strict=True
                    )
                ],
            )

    @_translate_errors
    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        if not self._indexed():
            return []
        found = self._connection.execute(
            "select source, position, start, length, file_hash, distance "
            "from cora_vectors join cora_passages using (id) "
            "where embedding match ? and k = ? and cora_vectors.scope = ? "
            "and user = ? order by distance",
            (sqlite_vec.serialize_float32(query_vector), k, scope, self._user),
        ).fetchall()
        return [
            RetrievedChunk(
                chunk=Chunk(
                    text="",
                    source=source,
                    index=position,
                    offset=start,
                    length=length,
                    upload=file_hash,
                    scope=scope,
                ),
                score=1.0 - distance,
            )
            for source, position, start, length, file_hash, distance in found
        ]

    @_translate_errors
    def sources(self, scope: str) -> list[str]:
        rows = self._connection.execute(
            "select source from cora_passages where user = ? and scope = ? order by id",
            (self._user, scope),
        ).fetchall()
        return list(dict.fromkeys(row[0] for row in rows))

    @_translate_errors
    def forget(self, scope: str, file_hash: str) -> None:
        with self._transaction():
            self._drop(scope, file_hash)

    @_translate_errors
    def uploads(self, scope: str, source: str) -> list[str]:
        rows = self._connection.execute(
            "select file_hash from cora_passages "
            "where user = ? and scope = ? and source = ? order by id",
            (self._user, scope, source),
        ).fetchall()
        return list(dict.fromkeys(row[0] for row in rows))

    @_translate_errors
    def contains(self, scope: str, file_hash: str) -> bool:
        found = self._connection.execute(
            "select 1 from cora_passages "
            "where user = ? and scope = ? and file_hash = ? limit 1",
            (self._user, scope, file_hash),
        ).fetchone()
        return found is not None

    def close(self) -> None:
        self._connection.close()

    def _transaction(self) -> sqlite3.Connection:
        """The connection is in autocommit, so `with connection` commits nothing on its
        own: the statement is what opens the transaction the block then closes."""
        self._connection.execute("begin")
        return self._connection

    def _drop(self, scope: str, file_hash: str) -> None:
        """Every passage of one upload, out of both tables. Read the ids first: the
        vector table is keyed by them and cannot be reached through the spans."""
        going = self._written(scope, file_hash)
        if not going:
            return
        if self._indexed():
            self._connection.executemany(
                "delete from cora_vectors where scope = ? and id = ?",
                [(scope, row_id) for row_id in going],
            )
        self._connection.executemany(
            "delete from cora_passages where id = ?", [(row_id,) for row_id in going]
        )

    def _written(self, scope: str, file_hash: str) -> list[int]:
        """This user's passage ids for one upload, in the order they were cut."""
        return [
            row[0]
            for row in self._connection.execute(
                "select id from cora_passages "
                "where user = ? and scope = ? and file_hash = ? order by id",
                (self._user, scope, file_hash),
            )
        ]

    def _indexed(self) -> bool:
        """Whether anything has been written yet: the vector table is the first write's
        doing, and a search before it is an empty field rather than a missing table."""
        return (
            self._connection.execute(
                "select 1 from sqlite_master "
                "where type = 'table' and name = 'cora_vectors'"
            ).fetchone()
            is not None
        )
