import datetime

from cora.plugins.vocab.schedule import Schedule
from cora.plugins.vocab.sm2 import Card

TODAY = datetime.date(2026, 9, 20)


def test_a_schedule_written_out_reads_back_the_same() -> None:
    schedule = Schedule().with_card(
        "help", Card(due=TODAY, interval=6, ease=2.6, right=2)
    )

    read = Schedule.of(schedule.written())

    assert read.card("help") == Card(due=TODAY, interval=6, ease=2.6, right=2)


def test_a_store_that_held_nothing_reads_as_an_empty_schedule() -> None:
    assert Schedule.of(None).card("help") == Card()


def test_text_that_is_not_a_schedule_reads_as_an_empty_one() -> None:
    assert Schedule.of("not a schedule at all").card("help") == Card()


def test_answering_one_word_leaves_every_other_alone() -> None:
    schedule = Schedule().with_card("help", Card(due=TODAY, interval=6))

    moved = schedule.with_card("house", Card(due=TODAY, interval=1))

    assert moved.card("help") == Card(due=TODAY, interval=6)
