import pytest

from docchat_plugins.fitness.calculators import (
    calculate_bmi,
    calculate_bmr,
    calculate_daily_energy,
)


@pytest.mark.parametrize(
    ("weight_kg", "height_m", "expected"),
    [
        (70.0, 1.75, 22.857142857142858),
        (95.0, 1.80, 29.320987654320987),
        (50.0, 1.70, 17.301038062283737),
    ],
)
def test_bmi_is_weight_over_height_squared(
    weight_kg: float, height_m: float, expected: float
) -> None:
    assert calculate_bmi(weight_kg, height_m) == pytest.approx(expected)


def test_male_bmr_matches_mifflin_st_jeor_reference() -> None:
    assert calculate_bmr("male", weight_kg=80, height_cm=180, age_years=30) == 1780.0


def test_female_bmr_matches_mifflin_st_jeor_reference() -> None:
    assert calculate_bmr("female", weight_kg=60, height_cm=165, age_years=25) == 1345.25


def test_daily_energy_returns_bmr_and_sedentary_tdee_reference() -> None:
    result = calculate_daily_energy(
        "male", weight_kg=80, height_cm=180, age_years=30, activity_level="sedentary"
    )

    assert result == {"bmr": 1780.0, "tdee": 2136.0}


@pytest.mark.parametrize(
    ("activity_level", "factor"),
    [
        ("sedentary", 1.2),
        ("lightly_active", 1.375),
        ("moderately_active", 1.55),
        ("very_active", 1.725),
        ("extra_active", 1.9),
    ],
)
def test_daily_energy_applies_each_activity_factor(
    activity_level: str, factor: float
) -> None:
    result = calculate_daily_energy(
        "male",
        weight_kg=80,
        height_cm=180,
        age_years=30,
        activity_level=activity_level,
    )

    assert result["tdee"] == pytest.approx(1780.0 * factor)
