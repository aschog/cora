import pytest

from cora.app.config import Config
from cora.domain.errors import ConfigurationError


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
            "CORA_DB_PATH": "/tmp/vectors",
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
        db_path="/tmp/vectors",
    )


def test_from_env_applies_defaults_for_optional_fields() -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.model
    assert config.base_url
    assert config.plugin_module
    assert config.top_k > 0
    assert config.max_tool_rounds > 0
    assert config.history_turns > 0
    assert config.db_path


def test_from_env_reads_retrieval_mode_and_fusion_queries() -> None:
    config = Config.from_env(
        {
            "OPENROUTER_API_KEY": "key-123",
            "CORA_RETRIEVAL": "advanced",
            "CORA_FUSION_QUERIES": "6",
        }
    )

    assert config.retrieval == "advanced"
    assert config.fusion_queries == 6


def test_from_env_defaults_to_plain_retrieval() -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.retrieval == "plain"
    assert config.fusion_queries >= 1


def test_from_env_accepts_hybrid_retrieval() -> None:
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "key-123", "CORA_RETRIEVAL": "hybrid"}
    )

    assert config.retrieval == "hybrid"


def test_from_env_rejects_an_unknown_retrieval_mode() -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", "CORA_RETRIEVAL": "bogus"})


def test_from_env_leaves_debug_off_when_the_flag_is_unset() -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.debug is False


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "True"])
def test_from_env_turns_debug_on_for_truthy_flags(raw: str) -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123", "CORA_DEBUG": raw})

    assert config.debug is True


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", ""])
def test_from_env_keeps_debug_off_for_falsy_flags(raw: str) -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123", "CORA_DEBUG": raw})

    assert config.debug is False


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
