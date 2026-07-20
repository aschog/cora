import dataclasses

import pytest

from docchat.chunk import Chunk


def test_chunks_are_equal_by_content() -> None:
    a = Chunk(text="hello", source="notes.txt", index=0, offset=0)
    b = Chunk(text="hello", source="notes.txt", index=0, offset=0)

    assert a == b


def test_chunks_differ_when_any_field_differs() -> None:
    base = Chunk(text="hello", source="notes.txt", index=0, offset=0)

    assert base != Chunk(text="world", source="notes.txt", index=0, offset=0)
    assert base != Chunk(text="hello", source="other.txt", index=0, offset=0)
    assert base != Chunk(text="hello", source="notes.txt", index=1, offset=0)
    assert base != Chunk(text="hello", source="notes.txt", index=0, offset=5)


def test_chunk_is_hashable_by_content() -> None:
    a = Chunk(text="hello", source="notes.txt", index=0, offset=0)
    b = Chunk(text="hello", source="notes.txt", index=0, offset=0)

    assert hash(a) == hash(b)
    assert {a, b} == {a}


def test_chunk_is_immutable() -> None:
    chunk = Chunk(text="hello", source="notes.txt", index=0, offset=0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        chunk.text = "changed"  # ty: ignore[invalid-assignment]
