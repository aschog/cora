import dataclasses

import pytest

from cora.domain.turn import Turn


def test_turns_are_equal_by_content() -> None:
    assert Turn(role="user", text="hi") == Turn(role="user", text="hi")
    assert Turn(role="user", text="hi") != Turn(role="assistant", text="hi")
    assert Turn(role="user", text="hi") != Turn(role="user", text="bye")


def test_turn_is_immutable() -> None:
    turn = Turn(role="user", text="hi")

    with pytest.raises(dataclasses.FrozenInstanceError):
        turn.text = "changed"  # ty: ignore[invalid-assignment]
