from cora.domain.chunk import Chunk


def test_chunk_is_hashable_by_content() -> None:
    a = Chunk(text="hello", source="notes.txt", index=0, offset=0)
    b = Chunk(text="hello", source="notes.txt", index=0, offset=0)

    assert hash(a) == hash(b)
    assert {a, b} == {a}
