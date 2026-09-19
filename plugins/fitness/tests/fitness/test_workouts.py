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
        ("Snatch day\nand more\n# Snatch 24 kg\n", 2, "one name line"),
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


def test_one_line_before_the_first_heading_is_the_sessions_name() -> None:
    titled = _parsed("Рывок гири\n\n# Swing 16 kg\n2 sets of 10\n")
    untitled = _parsed("# Swing 16 kg\n2 sets of 10\n")

    assert titled.name == "Рывок гири"
    assert [m.name for m in titled.movements] == ["Swing"]
    assert untitled.name == ""


# ── the tool: what the field holds, listed as text to show ──

MODULE = "cora.plugins.fitness"
DEADLIFT = "# Deadlift 14 kg\n3 sets of 10"
SWING = "# Swing 16 kg\n2 sets of 10"
SNATCH = "# Snatch 14 kg\nsets of 8 / 8"
PULL_UP = "# Pull-up bw+10\nsets of 5 / 5 / 4"
PLAN = "# 4-Week Beginner Strength Plan\n\nThree sessions a week."
SNATCH_WORKOUT = "Рывок гири"
TITLED = f"{SNATCH_WORKOUT}\n\n{SWING}"


def _listing(*documents: tuple[str, str], **asked: Any) -> str:
    held = [Document(name=name, text=text, scope="fitness") for name, text in documents]
    host = host_for(MODULE, documents=FakeContextSource(held=held))
    return list_workouts(host, **asked)


def _closing(days: int, saves: int) -> str:
    counted = (
        f"{days} day{'s' if days != 1 else ''}, {saves} save{'s' if saves != 1 else ''}"
    )
    return f"{counted}. The sets, reps and weights are in the details."


def test_every_document_named_for_a_day_is_a_session_dated_from_it_oldest_first() -> (
    None
):
    listed = _listing(("2026-09-18.md", DEADLIFT), ("2026-09-16.md", SWING))

    assert listed.splitlines()[:2] == [
        "2026-09-16: untitled save: Swing",
        "2026-09-18: untitled save: Deadlift",
    ]


def test_two_documents_of_one_day_are_one_session_in_upload_order() -> None:
    listed = _listing(("2026-09-18.md", DEADLIFT), ("2026-09-18.md", SNATCH))

    assert listed.splitlines()[0] == (
        "2026-09-18: untitled save: Deadlift · untitled save: Snatch"
    )


def test_unasked_for_detail_a_save_names_each_exercise_worked_once() -> None:
    listed = _listing(("2026-09-18.md", f"{SWING}\n\n{DEADLIFT}\n\n{SWING}"))

    assert listed.splitlines()[0] == "2026-09-18: untitled save: Swing · Deadlift"


def test_a_save_named_for_its_moment_and_its_workout_is_that_days_session() -> None:
    """The name carries the day, the time and then the workout, so a day's saves still
    sort by their moment and the rail says which workout each was."""
    listed = _listing((f"2026-09-18-16-20-05-{SNATCH_WORKOUT}.md", TITLED))

    assert listed.splitlines()[0].startswith("2026-09-18: ")


def test_a_day_names_its_workouts_first_and_an_untitled_save_marked() -> None:
    listed = _listing(
        ("2026-09-18-12-27-00.md", DEADLIFT),
        ("2026-09-18-16-20-05.md", TITLED),
        ("2026-09-18-16-42-10.md", f"{SNATCH_WORKOUT}\n\n{SNATCH}"),
    )

    assert listed.splitlines()[0] == (
        f"2026-09-18: {SNATCH_WORKOUT} · untitled save: Deadlift"
    )


def test_the_names_view_closes_with_what_it_holds_and_where_the_numbers_are() -> None:
    one = _listing(("2026-09-18.md", TITLED))
    more = _listing(
        ("2026-09-16.md", SWING), ("2026-09-18.md", TITLED), ("2026-09-18.md", SNATCH)
    )

    assert one == f"2026-09-18: {SNATCH_WORKOUT}\n{_closing(1, 1)}"
    assert more.splitlines()[-1] == _closing(2, 3)


def test_a_document_not_named_for_a_day_is_not_a_session() -> None:
    listed = _listing(("training-plan.md", PLAN), ("2026-09-16.md", SWING))

    assert listed == f"2026-09-16: untitled save: Swing\n{_closing(1, 1)}"


def test_a_dated_document_the_grammar_refuses_is_left_out_and_said_so() -> None:
    held = [
        Document(name="2026-09-17.md", text="# Snatch\n10 sets of 10", scope="fitness"),
        Document(name="2026-09-18.md", text=DEADLIFT, scope="fitness"),
    ]
    host = host_for(MODULE, documents=FakeContextSource(held=held))

    with collecting() as taken:
        listed = list_workouts(host)

    assert listed == f"2026-09-18: untitled save: Deadlift\n{_closing(1, 1)}"
    [skipped] = taken.steps
    assert skipped.failed
    assert "2026-09-17.md" in skipped.summary
    assert "2026-09-17.md:1:" in skipped.detail


def test_asked_for_detail_each_movement_is_a_line_with_its_numbers() -> None:
    listed = _listing(
        ("2026-09-16.md", SWING),
        ("2026-09-18.md", f"{DEADLIFT}\n\n{SNATCH}"),
        detail=True,
    )

    assert listed == (
        "2026-09-16\n"
        "- Swing — 16 kg · 2x10 · 20 reps · 320 kg\n"
        "\n"
        "2026-09-18\n"
        "- Deadlift — 14 kg · 3x10 · 30 reps · 420 kg\n"
        "- Snatch — 14 kg · 2x8 · 16 reps · 224 kg"
    )


def test_in_detail_the_days_line_carries_its_workouts_names() -> None:
    listed = _listing(
        ("2026-09-18.md", TITLED), ("2026-09-20.md", DEADLIFT), detail=True
    )

    assert listed.splitlines()[0] == f"2026-09-18 — {SNATCH_WORKOUT}"
    assert "2026-09-20\n- Deadlift" in listed


def test_a_bodyweight_movements_line_carries_its_reps_and_no_volume() -> None:
    listed = _listing(("2026-09-18.md", PULL_UP), detail=True)

    assert listed == "2026-09-18\n- Pull-up — bw+10 · 5+5+4 · 14 reps"


def test_a_movement_is_marked_where_it_rose_on_the_previous_session_of_it() -> None:
    days = (
        ("2026-09-16.md", "# Deadlift 14 kg\n3 sets of 10"),
        ("2026-09-18.md", "# Deadlift 14 kg\n3 sets of 12"),
        ("2026-09-20.md", "# Deadlift 16 kg\n3 sets of 8"),
        ("2026-09-22.md", "# Deadlift 16 kg\n3 sets of 8"),
    )

    listed = _listing(*days, detail=True)
    lately = _listing(*days, since="2026-09-18", detail=True)

    lines = [line for line in listed.splitlines() if line.startswith("- ")]
    assert [line.endswith(" ↑") for line in lines] == [False, True, True, False]
    # judged against the whole log, not against what the day narrowed it to
    assert lately.splitlines()[1].endswith(" ↑")


def test_an_exercise_and_a_day_narrow_both_views() -> None:
    days = (
        ("2026-09-16.md", SWING),
        ("2026-09-18.md", f"{DEADLIFT}\n\n{SNATCH}"),
        ("2026-09-20.md", TITLED),
        ("2026-09-20.md", DEADLIFT),
    )

    assert _listing(*days, exercise="deadlift") == (
        "2026-09-18: untitled save: Deadlift\n"
        f"2026-09-20: untitled save: Deadlift\n{_closing(2, 2)}"
    )
    assert _listing(*days, exercise="deadlift", since="2026-09-20", detail=True) == (
        "2026-09-20\n- Deadlift — 14 kg · 3x10 · 30 reps · 420 kg"
    )


def test_a_since_that_is_not_a_day_refuses_the_call() -> None:
    with pytest.raises(ToolRefusal, match="last week"):
        _listing(("2026-09-18.md", DEADLIFT), since="last week")


def test_nothing_logged_answers_in_words_rather_than_an_empty_list() -> None:
    assert _listing() == "No workout logged."
    assert _listing(("training-plan.md", PLAN)) == "No workout logged."
    assert _listing(("2026-09-18.md", DEADLIFT), exercise="snatch") == (
        "No workout logged with snatch."
    )
    assert _listing(("2026-09-18.md", DEADLIFT), since="2026-09-19") == (
        "No workout logged since 2026-09-19."
    )


def test_a_name_carrying_a_time_behind_the_day_is_a_session_of_that_day() -> None:
    listed = _listing(("2026-09-18-16-20-05.md", DEADLIFT))

    assert listed.splitlines()[0] == "2026-09-18: untitled save: Deadlift"


def test_a_days_saves_list_in_the_order_of_their_names_whatever_the_upload() -> None:
    listed = _listing(
        ("2026-09-18-16-42-10.md", SNATCH), ("2026-09-18-16-20-05.md", DEADLIFT)
    )

    assert listed.splitlines()[0] == (
        "2026-09-18: untitled save: Deadlift · untitled save: Snatch"
    )
