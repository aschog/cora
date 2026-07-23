def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / height_m**2


_SEX_CONSTANT = {"male": 5, "female": -161}


def calculate_bmr(
    sex: str, weight_kg: float, height_cm: float, age_years: int
) -> float:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age_years + _SEX_CONSTANT[sex]
