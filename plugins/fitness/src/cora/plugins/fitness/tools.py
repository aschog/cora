from cora.ports.plugin import Tool

from .calculators import (
    calculate_bmi,
    calculate_daily_energy,
    plan_macros,
)


def _bmi(weight_kg: float, height_m: float) -> float:
    return round(calculate_bmi(weight_kg, height_m), 1)


def _to_whole(values: dict[str, float]) -> dict[str, int]:
    return {key: round(value) for key, value in values.items()}


def _daily_energy(
    sex: str, weight_kg: float, height_cm: float, age_years: int, activity_level: str
) -> dict[str, int]:
    return _to_whole(
        calculate_daily_energy(sex, weight_kg, height_cm, age_years, activity_level)
    )


def _macros(kcal: float, weight_kg: float) -> dict[str, int]:
    return _to_whole(plan_macros(kcal, weight_kg))


_WEIGHT_KG = {"type": "number", "minimum": 20, "maximum": 300}

BMI_TOOL = Tool(
    name="calculate_bmi",
    description="Body Mass Index (kg/m²) from weight and height.",
    parameter_schema={
        "type": "object",
        "properties": {
            "weight_kg": _WEIGHT_KG,
            "height_m": {"type": "number", "minimum": 1.0, "maximum": 2.5},
        },
        "required": ["weight_kg", "height_m"],
    },
    run=_bmi,
)

DAILY_ENERGY_TOOL = Tool(
    name="calculate_daily_energy",
    description="Basal metabolic rate and total daily energy expenditure "
    "(Mifflin-St Jeor BMR scaled by an activity factor).",
    parameter_schema={
        "type": "object",
        "properties": {
            "sex": {"type": "string", "enum": ["male", "female"]},
            "weight_kg": _WEIGHT_KG,
            "height_cm": {"type": "number", "minimum": 100, "maximum": 250},
            "age_years": {"type": "integer", "minimum": 18, "maximum": 100},
            "activity_level": {
                "type": "string",
                "enum": [
                    "sedentary",
                    "lightly_active",
                    "moderately_active",
                    "very_active",
                    "extra_active",
                ],
            },
        },
        "required": [
            "sex",
            "weight_kg",
            "height_cm",
            "age_years",
            "activity_level",
        ],
    },
    run=_daily_energy,
)

MACROS_TOOL = Tool(
    name="plan_macros",
    description="Daily protein, fat, and carbohydrate grams for a calorie target.",
    parameter_schema={
        "type": "object",
        "properties": {
            "kcal": {"type": "number", "minimum": 1200, "maximum": 10000},
            "weight_kg": _WEIGHT_KG,
        },
        "required": ["kcal", "weight_kg"],
    },
    run=_macros,
)

TOOLS = (BMI_TOOL, DAILY_ENERGY_TOOL, MACROS_TOOL)
