import pytest

from cora.core.ports.plugin import ToolCall, ToolResult
from cora.core.services.tool_runtime import ToolRuntime
from cora.plugins.fitness.tools import TOOLS


def _run(name: str, arguments: dict[str, object]) -> ToolResult:
    return ToolRuntime(tools=TOOLS).execute(
        ToolCall(name=name, arguments=arguments, call_id="c1")
    )


def energy_args(**overrides: object) -> dict[str, object]:
    return {
        "sex": "male",
        "weight_kg": 80,
        "height_cm": 180,
        "age_years": 30,
        "activity_level": "sedentary",
    } | overrides


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("calculate_bmi", {"weight_kg": 10, "height_m": 1.75}),
        ("calculate_daily_energy", energy_args(age_years=16)),
        ("plan_macros", {"kcal": 1000, "weight_kg": 80}),
    ],
)
def test_out_of_range_args_return_an_error_result_not_a_raise(
    name: str, arguments: dict[str, object]
) -> None:
    result = _run(name, arguments)

    assert result.error is not None
    assert result.payload is None


@pytest.mark.parametrize(
    "arguments",
    [
        energy_args(activity_level="jetpacking"),
        energy_args(sex="alien"),
    ],
)
def test_invalid_enum_values_are_rejected_by_the_schema(
    arguments: dict[str, object],
) -> None:
    result = _run("calculate_daily_energy", arguments)

    assert result.payload is None
    assert "invalid arguments" in (result.error or "")


def test_macros_raise_surfaces_as_error_result_not_an_exception() -> None:
    # kcal 1200 / weight 150 pass the schema bounds but make carbs negative,
    # so plan_macros raises — the runtime must catch it, not propagate.
    result = _run("plan_macros", {"kcal": 1200, "weight_kg": 150})

    assert result.payload is None
    assert "calorie target" in (result.error or "")


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("calculate_bmi", {"weight_kg": 70, "height_m": 1.75}),
        ("calculate_daily_energy", energy_args()),
        ("plan_macros", {"kcal": 2500, "weight_kg": 80}),
    ],
)
def test_valid_call_returns_an_ok_result(
    name: str, arguments: dict[str, object]
) -> None:
    result = _run(name, arguments)

    assert result.error is None
    assert result.payload is not None


def test_bmi_tool_rounds_to_one_decimal() -> None:
    result = _run("calculate_bmi", {"weight_kg": 75, "height_m": 1.8})

    assert result.payload == 23.1
