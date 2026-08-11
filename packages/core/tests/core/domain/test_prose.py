from cora.core.domain.prose import counted, listed


def test_a_list_reads_as_english() -> None:
    assert listed([]) == ""
    assert listed(["a.txt"]) == "a.txt"
    assert listed(["a.txt", "b.txt"]) == "a.txt and b.txt"
    assert listed(["a.txt", "b.txt", "c.txt"]) == "a.txt, b.txt and c.txt"


def test_a_count_agrees_with_its_noun() -> None:
    assert counted(0, "passage") == "0 passages"
    assert counted(1, "passage") == "1 passage"
    assert counted(2, "passage") == "2 passages"
