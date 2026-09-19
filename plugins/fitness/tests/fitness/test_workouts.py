"""The grammar the trainer writes, read back as movements with their numbers."""

from datetime import date
from typing import Any

import pytest

from cora.engine.nesting import collecting
from cora.plugins.fitness.workouts import (
    Load,
    LogError,
    Session,
    list_workouts,
    parse_session,
)
from cora.ports.context_source import Document
from cora.ports.plugin import ToolRefusal
from fakes import FakeContextSource, host_for

DAY = date(2026, 9, 18)
# The sheet the trainer follows names its exercises in Russian, and this is one
# of them: the other script is the point, so the lint on lookalike letters is off.
ONE_ARM_SWING = "Мах одной рукой"  # noqa: RUF001


def _parsed(text: str) -> Session:
    return parse_session(text, DAY, "2026-09-18.md")


def test_a_heading_ending_in_kilograms_is_a_movement_with_that_name_and_load() -> None:
    deadlift, press = _parsed(
        "# Deadlift, conventional 14 kg\n\n# Press 12.5 kg\n"
    ).movements

    assert (deadlift.name, deadlift.load) == ("Deadlift, conventional", Load("kg", 14))
    assert press.load == Load("kg", 12.5)


def test_a_heading_ending_in_bw_or_bw_plus_reads_as_a_bodyweight_load() -> None:
    plain, weighted = _parsed("# Pull-up bw\n\n# Pull-up bw+10\n").movements

    assert plain.load == Load("bw", 0)
    assert weighted.load == Load("bw", 10)
    assert (str(plain.load), str(weighted.load)) == ("bw", "bw+10")


def test_repeated_sets_read_as_n_sets_of_r_and_listed_sets_as_each_in_turn() -> None:
    swing, pull = _parsed(
        "# Swing 16 kg\n3 sets of 10\n\n# Pull-up bw\nsets of 5 / 5 / 4\n"
    ).movements

    assert swing.sets == (10, 10, 10)
    assert pull.sets == (5, 5, 4)


def test_a_timed_line_reads_as_one_set_of_left_plus_right_reps() -> None:
    [snatch] = _parsed("# Snatch 24 kg\n10 min · 80 / 80\n").movements

    assert snatch.sets == (160,)


def test_a_line_that_is_neither_heading_nor_sets_is_a_note_on_the_movement() -> None:
    [swing] = _parsed("# Swing 32 kg\n10x10\n♥ 142 avg · 171 max · 41 min\n").movements

    assert swing.sets == ()
    assert swing.notes == ("10x10", "♥ 142 avg · 171 max · 41 min")


@pytest.mark.parametrize(
    ("text", "line", "fragment"),
    [
        ("hello\n# Snatch 24 kg\n", 1, "before the first heading"),
        ("# Snatch\n10 sets of 10\n", 1, "load"),
        ("# Snatch 24 kg\n10 sets of 10\nsets of 5 / 5\n", 3, "one set line"),
    ],
)
def test_a_document_the_grammar_refuses_is_refused_by_line(
    text: str, line: int, fragment: str
) -> None:
    with pytest.raises(LogError) as refused:
        _parsed(text)

    assert (refused.value.name, refused.value.line) == ("2026-09-18.md", line)
    assert fragment in refused.value.message
    assert str(refused.value).startswith(f"2026-09-18.md:{line}: ")


def test_reps_sum_the_sets_and_volume_is_load_times_reps_but_not_at_bodyweight() -> (
    None
):
    deadlift, pull = _parsed(
        "# Deadlift 14 kg\n3 sets of 10\n\n# Pull-up bw+10\nsets of 5 / 5 / 4\n"
    ).movements

    assert (deadlift.reps, deadlift.volume) == (30, 420)
    assert (pull.reps, pull.volume) == (14, None)


def test_a_heading_in_another_script_reads_as_any_other() -> None:
    [swing] = _parsed(f"# {ONE_ARM_SWING} 14 kg\n2 sets of 10\n").movements

    assert (swing.name, swing.load, swing.reps) == (ONE_ARM_SWING, Load("kg", 14), 20)


# ── the tool: what the field holds, listed ──

MODULE = "cora.plugins.fitness"
DEADLIFT = "# Deadlift 14 kg\n3 sets of 10"
SWING = "# Swing 16 kg\n2 sets of 10"
SNATCH = "# Snatch 14 kg\nsets of 8 / 8"
PLAN = "# 4-Week Beginner Strength Plan\n\nThree sessions a week."


def _listing(*documents: tuple[str, str], **filters: str) -> Any:
    held = [Document(name=name, text=text, scope="fitness") for name, text in documents]
    host = host_for(MODULE, documents=FakeContextSource(held=held))
    return list_workouts(host, **filters)


def _numbers(movement: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(movement[key] for key in ("name", "load", "sets", "reps", "volume_kg"))


def test_every_document_named_for_a_day_is_a_session_dated_from_it_oldest_first() -> (
    None
):
    listed = _listing(("2026-09-18.md", DEADLIFT), ("2026-09-16.md", SWING))

    assert [session["date"] for session in listed] == ["2026-09-16", "2026-09-18"]
    assert [_numbers(m) for m in listed[1]["movements"]] == [
        ("Deadlift", "14 kg", [10, 10, 10], 30, 420)
    ]


def test_two_documents_of_one_day_are_one_session_in_upload_order() -> None:
    listed = _listing(("2026-09-18.md", DEADLIFT), ("2026-09-18.md", SNATCH))

    [session] = listed
    assert [m["name"] for m in session["movements"]] == ["Deadlift", "Snatch"]


def test_a_document_not_named_for_a_day_is_not_a_session() -> None:
    listed = _listing(("training-plan.md", PLAN), ("2026-09-16.md", SWING))

    assert [session["date"] for session in listed] == ["2026-09-16"]


def test_a_dated_document_the_grammar_refuses_is_left_out_and_said_so() -> None:
    held = [
        Document(name="2026-09-17.md", text="# Snatch\n10 sets of 10", scope="fitness"),
        Document(name="2026-09-18.md", text=DEADLIFT, scope="fitness"),
    ]
    host = host_for(MODULE, documents=FakeContextSource(held=held))

    with collecting() as taken:
        listed = list_workouts(host)

    assert isinstance(listed, list)
    assert [session["date"] for session in listed] == ["2026-09-18"]
    [skipped] = taken.steps
    assert skipped.failed
    assert "2026-09-17.md" in skipped.summary
    assert "2026-09-17.md:1:" in skipped.detail


def test_an_exercise_keeps_only_its_movements_and_drops_a_session_left_empty() -> None:
    listed = _listing(
        ("2026-09-16.md", SWING),
        ("2026-09-18.md", f"{DEADLIFT}\n\n{SNATCH}"),
        exercise="deadlift",
    )

    assert [(s["date"], [m["name"] for m in s["movements"]]) for s in listed] == [
        ("2026-09-18", ["Deadlift"])
    ]


def test_a_day_drops_the_sessions_before_it() -> None:
    listed = _listing(
        ("2026-09-16.md", SWING), ("2026-09-18.md", DEADLIFT), since="2026-09-18"
    )

    assert [session["date"] for session in listed] == ["2026-09-18"]


def test_a_since_that_is_not_a_day_refuses_the_call() -> None:
    with pytest.raises(ToolRefusal, match="last week"):
        _listing(("2026-09-18.md", DEADLIFT), since="last week")


def test_a_movement_says_whether_it_rose_on_the_previous_session_of_it() -> None:
    days = (
        ("2026-09-16.md", "# Deadlift 14 kg\n3 sets of 10"),
        ("2026-09-18.md", "# Deadlift 14 kg\n3 sets of 12"),
        ("2026-09-20.md", "# Deadlift 16 kg\n3 sets of 8"),
        ("2026-09-22.md", "# Deadlift 16 kg\n3 sets of 8"),
    )

    listed = _listing(*days)
    lately = _listing(*days, since="2026-09-18")

    assert [s["movements"][0]["rose"] for s in listed] == [False, True, True, False]
    # judged against the whole log, not against what the day narrowed it to
    assert lately[0]["movements"][0]["rose"] is True


def test_nothing_logged_answers_in_words_rather_than_an_empty_list() -> None:
    assert _listing() == "No workout logged."
    assert _listing(("training-plan.md", PLAN)) == "No workout logged."
    assert _listing(("2026-09-18.md", DEADLIFT), exercise="snatch") == (
        "No workout logged with snatch."
    )
    assert _listing(("2026-09-18.md", DEADLIFT), since="2026-09-19") == (
        "No workout logged since 2026-09-19."
    )
