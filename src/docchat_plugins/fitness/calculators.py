def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / height_m**2


_SEX_CONSTANT = {"male": 5, "female": -161}

_ACTIVITY_FACTOR = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}


def calculate_bmr(
    sex: str, weight_kg: float, height_cm: float, age_years: int
) -> float:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age_years + _SEX_CONSTANT[sex]


def calculate_daily_energy(
    sex: str,
    weight_kg: float,
    height_cm: float,
    age_years: int,
    activity_level: str,
) -> dict[str, float]:
    bmr = calculate_bmr(sex, weight_kg, height_cm, age_years)
    return {"bmr": bmr, "tdee": bmr * _ACTIVITY_FACTOR[activity_level]}


def plan_macros(kcal: float, weight_kg: float) -> dict[str, float]:
    protein_g = 1.8 * weight_kg
    fat_g = 0.25 * kcal / 9
    carbs_g = (kcal - 4 * protein_g - 9 * fat_g) / 4
    return {"protein_g": protein_g, "fat_g": fat_g, "carbs_g": carbs_g}
