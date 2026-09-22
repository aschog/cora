import json
import sqlite3
from dataclasses import asdict
from typing import Any

from cora.adapters.sqlite_store import connect
from cora.adapters.translating import translating
from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.errors import ConversationStoreError
from cora.domain.trace import TraceStep, step_kinds

STEPS = "steps"

SCHEMA = (
    "create table if not exists cora_turns ("
    "id integer primary key autoincrement, thread text not null, turn text not null)"
)


# `OSError` is the directory the store could not be made in.
_translate_errors = translating((sqlite3.Error, OSError), ConversationStoreError)


class SqliteConversations:
    """One row per turn, in the order the turns were taken: the id the table hands out
    is what "the order they were taken" and "the newest conversation" both read off, so
    neither depends on a clock the tests would have to fake."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @classmethod
    @_translate_errors
    def at(cls, path: str) -> "SqliteConversations":
        connection = connect(path)
        connection.execute(SCHEMA)
        return cls(connection)

    @_translate_errors
    def record(self, thread_id: str, turn: Turn) -> None:
        self._connection.execute(
            "insert into cora_turns (thread, turn) values (?, ?)",
            (thread_id, json.dumps(_as_data(turn))),
        )

    @_translate_errors
    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        rows = self._connection.execute(
            "select turn from cora_turns where thread = ? order by id", (thread_id,)
        ).fetchall()
        return tuple(_from_data(json.loads(row[0])) for row in rows)

    @_translate_errors
    def sessions(self) -> tuple[Session, ...]:
        rows = self._connection.execute(
            "select thread, turn from cora_turns where id in "
            "(select min(id) from cora_turns group by thread) "
            "order by (select max(id) from cora_turns as newest where newest.thread = "
            "cora_turns.thread) desc"
        ).fetchall()
        return tuple(
            Session(thread_id=row[0], opened_with=json.loads(row[1])["question"])
            for row in rows
        )

    @_translate_errors
    def forget(self, thread_id: str) -> None:
        self._connection.execute(
            "delete from cora_turns where thread = ?", (thread_id,)
        )

    def close(self) -> None:
        self._connection.close()


def _as_data(turn: Turn) -> dict[str, Any]:
    return {
        "question": turn.question,
        "answer": turn.result.answer,
        "citations": [asdict(citation) for citation in turn.result.citations],
        "trace": [_as_step(step) for step in turn.result.trace],
        "scopes": list(turn.result.scopes),
    }


def _from_data(data: dict[str, Any]) -> Turn:
    return Turn(
        question=str(data["question"]),
        result=ChatResult(
            answer=str(data["answer"]),
            citations=tuple(Citation(**found) for found in data["citations"]),
            trace=tuple(_step(step) for step in data["trace"]),
            # A turn recorded before a turn carried its fields has none, and reads back
            # as a turn in no named field — which is what it was.
            scopes=tuple(data.get("scopes", ())),
        ),
    )


def _as_step(step: TraceStep) -> dict[str, Any]:
    # Every kind of step is a frozen dataclass; `TraceStep` itself is the ABC they
    # share, which ty cannot read as a dataclass instance.
    fields = asdict(step)  # ty: ignore[invalid-argument-type]
    if step.steps:
        fields[STEPS] = [_as_step(child) for child in step.steps]
    return {"kind": type(step).__name__, "fields": fields}


def _step(data: dict[str, Any]) -> TraceStep:
    kind = {step.__name__: step for step in step_kinds()}[data["kind"]]
    return kind(
        **{
            name: tuple(_step(child) for child in value) if name == STEPS else value
            for name, value in data["fields"].items()
        }
    )
