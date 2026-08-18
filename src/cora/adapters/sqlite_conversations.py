import json
import pathlib
import sqlite3
from collections.abc import Callable
from functools import wraps

from cora.domain.chat_result import ChatResult
from cora.domain.conversation import Session, Turn
from cora.domain.errors import ConversationStoreError

SCHEMA = (
    "create table if not exists turns ("
    "id integer primary key autoincrement, thread text not null, turn text not null)"
)


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except sqlite3.Error as error:
            raise ConversationStoreError() from error

    return wrapper


class SqliteConversations:
    """One row per turn, in the order the turns were taken: the id the table hands out
    is what "the order they were taken" and "the newest conversation" both read off, so
    neither depends on a clock the tests would have to fake."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @classmethod
    @_translate_errors
    def at(cls, path: str) -> "SqliteConversations":
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None
        )
        connection.execute(SCHEMA)
        return cls(connection)

    @_translate_errors
    def record(self, thread_id: str, turn: Turn) -> None:
        self._connection.execute(
            "insert into turns (thread, turn) values (?, ?)",
            (thread_id, json.dumps(_as_data(turn))),
        )

    @_translate_errors
    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        rows = self._connection.execute(
            "select turn from turns where thread = ? order by id", (thread_id,)
        ).fetchall()
        return tuple(_from_data(json.loads(row[0])) for row in rows)

    @_translate_errors
    def sessions(self) -> tuple[Session, ...]:
        rows = self._connection.execute(
            "select thread, turn from turns where id in "
            "(select min(id) from turns group by thread) "
            "order by (select max(id) from turns as newest where newest.thread = "
            "turns.thread) desc"
        ).fetchall()
        return tuple(
            Session(thread_id=row[0], opened_with=json.loads(row[1])["question"])
            for row in rows
        )

    def close(self) -> None:
        self._connection.close()


def _as_data(turn: Turn) -> dict[str, object]:
    return {"question": turn.question, "answer": turn.result.answer}


def _from_data(data: dict[str, object]) -> Turn:
    return Turn(
        question=str(data["question"]),
        result=ChatResult(answer=str(data["answer"])),
    )
