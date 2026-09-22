from cora.domain.chunk import Chunk


def test_chunk_is_hashable_by_content() -> None:
    a = Chunk(text="hello", source="notes.txt", index=0, offset=0)
    b = Chunk(text="hello", source="notes.txt", index=0, offset=0)

    assert hash(a) == hash(b)
    assert {a, b} == {a}


def test_a_chunk_measures_its_own_text_whatever_length_it_was_given() -> None:
    assert Chunk(text="abcd", source="doc.md", index=0, offset=0, length=99).length == 4


def test_a_chunk_read_back_from_the_index_keeps_the_length_it_was_given() -> None:
    assert Chunk(text="", source="doc.md", index=0, offset=0, length=42).length == 42
