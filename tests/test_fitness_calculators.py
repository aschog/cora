import pytest

from docchat_plugins.fitness.calculators import calculate_bmi


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
