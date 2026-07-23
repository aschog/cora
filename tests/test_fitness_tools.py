import pytest

from docchat.plugin import ToolCall, ToolResult
from docchat.tool_runtime import ToolRuntime
from docchat_plugins.fitness.tools import TOOLS


def _run(name: str, arguments: dict[str, object]) -> ToolResult:
    return ToolRuntime(tools=TOOLS).execute(
        ToolCall(name=name, arguments=arguments, call_id="c1")
    )


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("calculate_bmi", {"weight_kg": 10, "height_m": 1.75}),
        (
            "calculate_daily_energy",
            {
                "sex": "male",
                "weight_kg": 80,
                "height_cm": 180,
                "age_years": 16,
                "activity_level": "sedentary",
            },
        ),
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
        {
            "sex": "male",
            "weight_kg": 80,
            "height_cm": 180,
            "age_years": 30,
            "activity_level": "jetpacking",
        },
        {
            "sex": "alien",
            "weight_kg": 80,
            "height_cm": 180,
            "age_years": 30,
            "activity_level": "sedentary",
        },
    ],
)
def test_invalid_enum_values_are_rejected_by_the_schema(
    arguments: dict[str, object],
) -> None:
    result = _run("calculate_daily_energy", arguments)

    assert result.payload is None
    assert "invalid arguments" in (result.error or "")
