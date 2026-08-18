from pathlib import Path

from cora.adapters.sqlite_conversations import SqliteConversations
from cora.domain.chat_result import ChatResult
from cora.domain.conversation import Turn

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


def test_the_turns_of_a_conversation_read_back_in_the_order_they_were_taken(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    later = Turn(question="And creatine?", result=ChatResult(answer="Five grams."))

    store.record(THREAD, TURN)
    store.record(THREAD, later)

    assert store.turns(THREAD) == (TURN, later)
