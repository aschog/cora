import datetime

from cora.plugins.vocab.sm2 import EASE_FLOOR, FIRST, SECOND, Card, due, reviewed

TODAY = datetime.date(2026, 9, 20)


def test_a_word_answered_right_the_first_time_comes_back_tomorrow() -> None:
    moved = reviewed(Card(), right=True, today=TODAY)

    assert moved.interval == FIRST
    assert moved.due == TODAY + datetime.timedelta(days=FIRST)


def test_a_word_answered_right_again_comes_back_in_six_days_then_by_its_ease() -> None:
    once = reviewed(Card(), right=True, today=TODAY)
    twice = reviewed(once, right=True, today=TODAY)

    thrice = reviewed(twice, right=True, today=TODAY)

    assert (once.interval, twice.interval) == (FIRST, SECOND)
    assert thrice.interval == round(SECOND * twice.ease)


def test_a_word_missed_comes_back_in_this_session_whatever_it_had_earned() -> None:
    """Not tomorrow and not in six days: the reader is sitting there, and the word they
    just failed is the word to ask again."""
    known = reviewed(reviewed(Card(), right=True, today=TODAY), right=True, today=TODAY)

    missed = reviewed(known, right=False, today=TODAY)

    assert missed.interval == 0
    assert missed.due == TODAY
    assert due(missed, TODAY)


def test_a_miss_lowers_the_ease_and_the_ease_has_a_floor() -> None:
    card = Card()

    for _ in range(20):
        card = reviewed(card, right=False, today=TODAY)

    assert card.ease == EASE_FLOOR


def test_a_word_never_drilled_is_due() -> None:
    assert due(Card(), TODAY)


def test_a_word_scheduled_beyond_today_is_not_due() -> None:
    assert not due(reviewed(Card(), right=True, today=TODAY), TODAY)
