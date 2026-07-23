def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / height_m**2


def calculate_bmr(
    sex: str, weight_kg: float, height_cm: float, age_years: int
) -> float:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
