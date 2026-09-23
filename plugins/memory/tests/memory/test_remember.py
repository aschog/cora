import pytest

from cora.domain.errors import MemoryStoreError
from cora.plugins.memory.remember import MAX_FACT_CHARS, RememberFact
from cora.ports.plugin import ToolRefusal
from fakes import FailingMemory, FakeMemory


def test_the_tool_stores_the_fact_the_model_passed() -> None:
    memory = FakeMemory()

    confirmation = RememberFact(memory)("trains on Tuesdays")

    assert [fact.text for fact in memory.recall()] == ["trains on Tuesdays"]
    assert "trains on Tuesdays" in confirmation


def test_a_store_that_cannot_be_written_refuses_rather_than_ending_the_turn() -> None:
    with pytest.raises(ToolRefusal, match=MemoryStoreError().user_message):
        RememberFact(FailingMemory(MemoryStoreError()))("x")


def test_a_fact_longer_than_the_bound_is_refused() -> None:
    memory = FakeMemory()

    with pytest.raises(ToolRefusal, match=str(MAX_FACT_CHARS)):
        RememberFact(memory)("x" * (MAX_FACT_CHARS + 1))

    assert memory.recall() == ()


def test_a_fact_already_known_is_not_kept_twice() -> None:
    memory = FakeMemory(("trains on Tuesdays",))

    said = RememberFact(memory)("trains on Tuesdays")

    assert [fact.text for fact in memory.recall()] == ["trains on Tuesdays"]
    assert said.startswith("Already")


def test_an_empty_fact_is_refused() -> None:
    memory = FakeMemory()

    with pytest.raises(ToolRefusal):
        RememberFact(memory)("   ")

    assert memory.recall() == ()
