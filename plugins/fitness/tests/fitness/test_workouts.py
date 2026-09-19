"""The grammar the trainer writes, read back as movements with their numbers."""

from datetime import date

import pytest

from cora.plugins.fitness.workouts import Load, LogError, Session, parse_session

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
