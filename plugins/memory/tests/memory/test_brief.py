from cora.plugins.memory.brief import (
    HELD_AT_SEVERAL,
    REMEMBERED_HEADING,
    REMEMBERED_NOTICE,
    remembered,
)
from cora.ports.memory import Fact

HELD_THREE_WAYS = (
    "bodyweight 77 kg, from the intake form on 17 August",
    "bodyweight 75 kg, from the coach notes in February",
    "bodyweight 85 kg, from the physio letter",
)


def _facts(*texts: str) -> tuple[Fact, ...]:
    return tuple(Fact(key=f"f{at}", text=text) for at, text in enumerate(texts))


def test_the_notes_are_appended_under_their_heading_behind_the_notice() -> None:
    brief = remembered("SYS", _facts("trains on Tuesdays", "is vegetarian"))

    assert brief.startswith("SYS\n\n")
    assert brief.index(REMEMBERED_NOTICE) < brief.index(REMEMBERED_HEADING)
    assert "- trains on Tuesdays\n- is vegetarian" in brief


def test_no_notes_leave_the_brief_as_it_was() -> None:
    assert remembered("SYS", ()) == "SYS"


def test_a_fact_the_notes_hold_at_several_values_is_named_as_one() -> None:
    brief = remembered("SYS", _facts(*HELD_THREE_WAYS))

    assert HELD_AT_SEVERAL.format(subject="bodyweight", count=3) in brief
    assert "ask_user" in brief


def test_notes_that_agree_are_not_reported_as_a_conflict() -> None:
    settled = (
        "bodyweight 75 kg, from the coach notes",
        "bodyweight 75 kg, from the intake form",
        "trains four times a week",
    )

    assert "held at" not in remembered("SYS", _facts(*settled)).lower()


def test_a_subject_held_once_is_not_reported() -> None:
    once = ("bodyweight 75 kg", "trains four times a week")

    assert "held at" not in remembered("SYS", _facts(*once)).lower()
