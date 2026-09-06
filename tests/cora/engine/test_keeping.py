"""What a plugin kept for the conversation the work happening now belongs to."""

from cora.engine import keeping

KEEPER = "keeper"
OTHER = "birds"
NOTE = "note"
KYOTO = "Kyoto in May"


def test_a_name_kept_reads_back() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, KYOTO)

        assert keeping.read(KEEPER, NOTE) == KYOTO


def test_a_name_nothing_was_kept_under_reads_as_nothing() -> None:
    with keeping.bound({}):
        assert keeping.read(KEEPER, NOTE) is None


def test_keeping_nothing_under_a_name_drops_it() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, KYOTO)
        keeping.keep(KEEPER, NOTE, None)

        assert keeping.read(KEEPER, NOTE) is None


def test_dropping_a_name_nothing_was_kept_under_is_not_an_error() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, None)

        assert keeping.read(KEEPER, NOTE) is None


def test_two_plugins_keep_the_same_name_apart() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, KYOTO)
        keeping.keep(OTHER, NOTE, "a wren")

        assert keeping.read(KEEPER, NOTE) == KYOTO
        assert keeping.read(OTHER, NOTE) == "a wren"


def test_what_was_kept_is_written_into_the_dictionary_bound() -> None:
    kept: dict[str, dict[str, str]] = {}

    with keeping.bound(kept):
        keeping.keep(KEEPER, NOTE, KYOTO)

    assert kept == {KEEPER: {NOTE: KYOTO}}


def test_a_binding_reads_what_it_was_handed() -> None:
    with keeping.bound({KEEPER: {NOTE: KYOTO}}):
        assert keeping.read(KEEPER, NOTE) == KYOTO


def test_a_read_outside_a_binding_comes_back_with_nothing() -> None:
    assert keeping.read(KEEPER, NOTE) is None


def test_a_write_outside_a_binding_is_dropped() -> None:
    keeping.keep(KEEPER, NOTE, KYOTO)

    assert keeping.read(KEEPER, NOTE) is None


def test_a_binding_is_reset_when_it_ends() -> None:
    with keeping.bound({KEEPER: {NOTE: KYOTO}}):
        pass

    assert keeping.read(KEEPER, NOTE) is None


def test_a_binding_inside_another_leaves_the_outer_one_as_it_was() -> None:
    outer: dict[str, dict[str, str]] = {}

    with keeping.bound(outer):
        keeping.keep(KEEPER, NOTE, KYOTO)
        with keeping.bound({}):
            assert keeping.read(KEEPER, NOTE) is None
        assert keeping.read(KEEPER, NOTE) == KYOTO
