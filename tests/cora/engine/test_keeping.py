from cora.engine import keeping

KEEPER = "keeper"
OTHER = "birds"
NOTE = "note"
KYOTO = "Kyoto in May"


def test_a_name_kept_reads_back() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, KYOTO)

        assert keeping.read(KEEPER, NOTE) == KYOTO


def test_keeping_nothing_under_a_name_drops_it() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, KYOTO)
        keeping.keep(KEEPER, NOTE, None)

        assert keeping.read(KEEPER, NOTE) is None


def test_two_plugins_keep_the_same_name_apart() -> None:
    with keeping.bound({}):
        keeping.keep(KEEPER, NOTE, KYOTO)
        keeping.keep(OTHER, NOTE, "a wren")

        assert keeping.read(KEEPER, NOTE) == KYOTO
        assert keeping.read(OTHER, NOTE) == "a wren"


def test_a_write_outside_a_binding_is_dropped() -> None:
    keeping.keep(KEEPER, NOTE, KYOTO)

    assert keeping.read(KEEPER, NOTE) is None


def test_a_binding_inside_another_leaves_the_outer_one_as_it_was() -> None:
    outer: dict[str, dict[str, str]] = {}

    with keeping.bound(outer):
        keeping.keep(KEEPER, NOTE, KYOTO)
        with keeping.bound({}):
            assert keeping.read(KEEPER, NOTE) is None
        assert keeping.read(KEEPER, NOTE) == KYOTO
