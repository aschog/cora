"""The grammar the trainer writes, read back as movements with their numbers."""

from datetime import date

from cora.plugins.fitness.workouts import Load, Session, parse_session

DAY = date(2026, 9, 18)


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
