import sqlite3
from pathlib import Path

import pytest

from cora.adapters.sqlite_conversations import SqliteConversations
from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.errors import ConversationStoreError
from cora.domain.trace import (
    MemoryUnread,
    ModelDecision,
    StepEntered,
    ToolUse,
)

THREAD = "9f1c0f7a-0d5e-4a3a-9d0f-1b2c3d4e5f60"
ASKED = "How much protein should I eat?"
TURN = Turn(question=ASKED, result=ChatResult(answer="Your notes say 1.6 g per kg."))


def _store(tmp_path: Path, name: str = "conversations.sqlite") -> SqliteConversations:
    return SqliteConversations.at(str(tmp_path / name))


def test_a_turn_reads_back_unchanged(tmp_path: Path) -> None:
    store = _store(tmp_path)

    store.record(THREAD, TURN)

    assert store.turns(THREAD) == (TURN,)


def test_a_conversation_survives_the_database_being_reopened(tmp_path: Path) -> None:
    """The whole point of the store: a conversation the reader comes back to is one the
    process that held it no longer exists for."""
    first = _store(tmp_path)
    first.record(THREAD, TURN)
    first.close()

    assert _store(tmp_path).turns(THREAD) == (TURN,)


def test_sessions_are_listed_newest_first_named_by_what_opened_them(
    tmp_path: Path,
) -> None:
    """A reader picks a conversation out of a list by what it was about, and the thread
    id says nothing. Newest first, because that is the end a list is read from."""
    store = _store(tmp_path)
    store.record("older", TURN)
    store.record(
        "newer", Turn(question="And creatine?", result=ChatResult(answer="5 g"))
    )

    assert store.sessions() == (
        Session(thread_id="newer", opened_with="And creatine?"),
        Session(thread_id="older", opened_with=ASKED),
    )


def test_a_forgotten_conversation_has_no_turns(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.record(THREAD, TURN)

    store.forget(THREAD)

    assert store.turns(THREAD) == ()


def test_a_driver_failure_surfaces_as_an_adapter_error(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.close()

    with pytest.raises(ConversationStoreError):
        store.record(THREAD, TURN)


CITATION = Citation(
    number=1, document="protein.md", start=10, end=40, upload="3f786850e3"
)
TRACED = Turn(
    question=ASKED,
    result=ChatResult(
        answer="Your notes say 1.6 g per kg [1].",
        citations=(CITATION,),
        trace=(
            StepEntered("screen"),
            StepEntered("work"),
            ModelDecision(tools=("search_documents",)),
            ToolUse(
                name="search_documents",
                arguments={"query": "protein"},
                outcome="1 passage",
                detail="[1] protein.md: aim for 1.6 g",
            ),
            StepEntered("answer"),
        ),
    ),
)


def test_a_turn_keeps_its_citations_and_its_trace(tmp_path: Path) -> None:
    """A conversation reopened is one whose numbers can still be clicked and whose plan
    can still be read, so what a turn rested on travels with it — not just its prose."""
    store = _store(tmp_path)

    store.record(THREAD, TRACED)

    assert store.turns(THREAD) == (TRACED,)


def test_a_kind_of_step_the_store_never_heard_of_still_round_trips(
    tmp_path: Path,
) -> None:
    """Steps are found rather than listed, as the checkpoint's allowlist already is: a
    kind added next sprint is storable without anyone remembering this file."""
    store = _store(tmp_path)
    turn = Turn(
        question=ASKED,
        result=ChatResult(answer="none", trace=(MemoryUnread(),)),
    )

    store.record(THREAD, turn)

    assert store.turns(THREAD) == (turn,)


def test_a_step_that_carries_children_keeps_them(tmp_path: Path) -> None:
    """What a plugin's tool did inside a call is part of that call, so a conversation
    reopened shows the same tree it showed when the turn was answered."""
    store = _store(tmp_path)
    nested = Turn(
        question=ASKED,
        result=ChatResult(
            answer="Sleep, not volume.",
            trace=(
                ToolUse(
                    name="research",
                    arguments={"question": "why?"},
                    outcome="answered",
                    steps=(ModelDecision(tools=("search_documents",)),),
                ),
            ),
        ),
    )

    store.record(THREAD, nested)

    [kept] = store.turns(THREAD)
    [call] = kept.result.trace
    assert [step.summary for step in call.steps] == ["Decided to call search_documents"]


def test_the_store_shares_the_file_in_write_ahead_mode(tmp_path: Path) -> None:
    """Four writers share this file, and the default journal takes an exclusive lock
    that blocks readers for the length of a write. The turns are one of the four, so
    the mode cannot depend on which of them opened it first."""
    store = SqliteConversations.at(str(tmp_path / "cora.sqlite"))

    with sqlite3.connect(str(tmp_path / "cora.sqlite")) as reading:
        [(mode,)] = reading.execute("pragma journal_mode")

    store.close()
    assert mode == "wal"
