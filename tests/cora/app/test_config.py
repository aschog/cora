import pytest

from cora.app.config import Config
from cora.core.errors import ConfigurationError


def test_from_env_reads_every_field() -> None:
    config = Config.from_env(
        {
            "OPENROUTER_API_KEY": "key-123",
            "CORA_MODEL": "anthropic/claude",
            "OPENROUTER_BASE_URL": "https://example/api",
            "CORA_PLUGIN": "cora.plugins.custom",
            "CORA_TOP_K": "7",
            "CORA_MAX_TOOL_ROUNDS": "3",
            "CORA_HISTORY_TURNS": "9",
        }
    )

    assert config == Config(
        api_key="key-123",
        model="anthropic/claude",
        base_url="https://example/api",
        plugin_module="cora.plugins.custom",
        top_k=7,
        max_tool_rounds=3,
        history_turns=9,
    )


def test_from_env_applies_defaults_for_optional_fields() -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.model
    assert config.base_url
    assert config.plugin_module
    assert config.top_k > 0
    assert config.max_tool_rounds > 0
    assert config.history_turns > 0


def test_from_env_missing_api_key_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({})


@pytest.mark.parametrize(
    "var", ["CORA_TOP_K", "CORA_MAX_TOOL_ROUNDS", "CORA_HISTORY_TURNS"]
)
def test_from_env_non_integer_value_raises_configuration_error(var: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", var: "lots"})


@pytest.mark.parametrize(
    "var", ["CORA_TOP_K", "CORA_MAX_TOOL_ROUNDS", "CORA_HISTORY_TURNS"]
)
def test_from_env_negative_value_raises_configuration_error(var: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", var: "-1"})


@pytest.mark.parametrize("var", ["CORA_TOP_K", "CORA_MAX_TOOL_ROUNDS"])
def test_from_env_zero_raises_where_one_is_the_lowest_useful_value(var: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", var: "0"})


def test_from_env_allows_zero_history_turns_to_switch_memory_off() -> None:
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "key-123", "CORA_HISTORY_TURNS": "0"}
    )

    assert config.history_turns == 0
