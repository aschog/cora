from cora.app.retrieval import RETRIEVAL_BUILDERS, RETRIEVAL_MODES


def test_allowed_modes_are_exactly_the_registered_builders() -> None:
    assert tuple(RETRIEVAL_BUILDERS) == RETRIEVAL_MODES
