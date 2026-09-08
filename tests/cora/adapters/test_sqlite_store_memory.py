import pathlib
import sqlite3

import pytest

from cora.adapters.sqlite_store_memory import RECALL_LIMIT, SqliteStoreMemory
from cora.domain.errors import AdapterError, MemoryStoreError


@pytest.fixture
def path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "memory.sqlite")


def test_a_fact_survives_a_new_adapter_over_the_same_file(path: str) -> None:
    """The reopen in miniature: what the criterion means by "last session"."""
    SqliteStoreMemory.at(path).remember("trains on Tuesdays")

    facts = SqliteStoreMemory.at(path).recall()

    assert [fact.text for fact in facts] == ["trains on Tuesdays"]


def test_facts_come_back_oldest_first_under_stable_keys(path: str) -> None:
    memory = SqliteStoreMemory.at(path)

    memory.remember("trains on Tuesdays")
    memory.remember("is vegetarian")

    keys = [fact.key for fact in memory.recall()]
    assert [fact.text for fact in memory.recall()] == [
        "trains on Tuesdays",
        "is vegetarian",
    ]
    assert keys == [fact.key for fact in SqliteStoreMemory.at(path).recall()]


def test_forgetting_removes_that_fact_alone(path: str) -> None:
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.remember("is vegetarian")

    memory.forget(memory.recall()[0].key)

    assert [fact.text for fact in SqliteStoreMemory.at(path).recall()] == [
        "is vegetarian"
    ]


def test_clearing_removes_them_all(path: str) -> None:
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.remember("is vegetarian")

    memory.clear()

    assert SqliteStoreMemory.at(path).recall() == ()


def test_another_user_recalls_nothing(path: str) -> None:
    """The namespace is the adapter's, so authentication later is a constructor
    argument rather than a change to the port."""
    SqliteStoreMemory.at(path, user="ada").remember("trains on Tuesdays")

    assert SqliteStoreMemory.at(path, user="grace").recall() == ()
    assert len(SqliteStoreMemory.at(path, user="ada").recall()) == 1


def test_a_fresh_path_creates_its_directories(tmp_path: pathlib.Path) -> None:
    nested = tmp_path / "does" / "not" / "exist" / "memory.sqlite"

    SqliteStoreMemory.at(str(nested)).remember("trains on Tuesdays")

    assert nested.exists()


def test_opening_the_same_file_twice_is_harmless(path: str) -> None:
    first = SqliteStoreMemory.at(path)
    second = SqliteStoreMemory.at(path)

    first.remember("trains on Tuesdays")

    assert [fact.text for fact in second.recall()] == ["trains on Tuesdays"]


def test_a_broken_database_surfaces_as_an_adapter_error(path: str) -> None:
    """So the friendly-failure path holds: the UI renders `user_message`, never a
    sqlite traceback."""
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.close()

    with pytest.raises(AdapterError):
        memory.recall()
    with pytest.raises(AdapterError):
        memory.remember("is vegetarian")


MORE_THAN_A_PAGE = 150


def test_clearing_removes_more_facts_than_one_page_holds(path: str) -> None:
    """`clear` used to read one page and delete what it had read, so "forget
    everything" left everything past the page behind and the panel repopulated."""
    memory = SqliteStoreMemory.at(path)
    for number in range(MORE_THAN_A_PAGE):
        memory.remember(f"fact {number}")

    memory.clear()

    assert SqliteStoreMemory.at(path).recall() == ()


def test_recall_returns_the_newest_facts_when_there_are_more_than_it_shows(
    path: str,
) -> None:
    """The window has to be the newest, and it has to be a decision: the store orders
    by a timestamp that ties at one second, so an unordered page handed back whatever
    the query planner yielded — in practice the oldest, which no one can delete
    because it is the newest that are hidden."""
    memory = SqliteStoreMemory.at(path)
    for number in range(MORE_THAN_A_PAGE):
        memory.remember(f"fact {number}")

    facts = memory.recall()

    assert len(facts) == RECALL_LIMIT
    assert facts[-1].text == f"fact {MORE_THAN_A_PAGE - 1}"
    assert facts[0].text == f"fact {MORE_THAN_A_PAGE - RECALL_LIMIT}"


def test_a_forgotten_fact_makes_room_for_a_hidden_one(path: str) -> None:
    """The window is what the user can act on, so what falls outside it has to come
    back into view once there is room — otherwise a hidden fact is unreachable."""
    memory = SqliteStoreMemory.at(path)
    for number in range(RECALL_LIMIT + 1):
        memory.remember(f"fact {number}")
    shown = memory.recall()

    assert "fact 0" not in [fact.text for fact in shown]

    memory.forget(shown[-1].key)

    assert "fact 0" in [fact.text for fact in memory.recall()]


def test_the_store_shares_the_file_in_write_ahead_mode(
    tmp_path: pathlib.Path,
) -> None:
    """As the turns beside it: whichever of the four stores opens the shared file, it is
    opened in the mode that lets the others read while one writes."""
    memory = SqliteStoreMemory.at(str(tmp_path / "cora.sqlite"))

    with sqlite3.connect(str(tmp_path / "cora.sqlite")) as reading:
        [(mode,)] = reading.execute("pragma journal_mode")

    memory.close()
    assert mode == "wal"


def test_a_path_whose_directory_cannot_be_made_surfaces_as_memory_error(
    tmp_path: pathlib.Path,
) -> None:
    """As the two stores beside it in the same file."""
    blocked = tmp_path / "a-file"
    blocked.write_text("not a directory")

    with pytest.raises(MemoryStoreError):
        SqliteStoreMemory.at(str(blocked / "cora.sqlite"))
