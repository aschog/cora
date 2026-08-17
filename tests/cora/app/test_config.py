from pathlib import Path

import pytest

from cora.app.config import DEFAULT_MEMORY_PATH, DEFAULT_PLUGINS, Config
from cora.domain.errors import ConfigurationError


def test_from_env_reads_every_field() -> None:
    config = Config.from_env(
        {
            "OPENROUTER_API_KEY": "key-123",
            "CORA_MODEL": "anthropic/claude",
            "OPENROUTER_BASE_URL": "https://example/api",
            "CORA_PLUGINS": "cora.plugins.custom",
            "CORA_TOP_K": "7",
            "CORA_MAX_TOOL_ROUNDS": "3",
            "CORA_HISTORY_TURNS": "9",
            "CORA_DB_PATH": "/tmp/vectors",
            "CORA_MEMORY_PATH": "/tmp/memory.sqlite",
        }
    )

    assert config == Config(
        api_key="key-123",
        model="anthropic/claude",
        base_url="https://example/api",
        plugin_modules=("cora.plugins.custom",),
        top_k=7,
        max_tool_rounds=3,
        history_turns=9,
        db_path="/tmp/vectors",
        memory_path="/tmp/memory.sqlite",
    )


def test_from_env_applies_defaults_for_optional_fields() -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.model
    assert config.base_url
    assert config.plugin_modules == DEFAULT_PLUGINS
    assert config.top_k > 0
    assert config.max_tool_rounds > 0
    assert config.history_turns > 0
    assert config.db_path
    assert config.memory_path


def test_the_model_may_be_named_with_the_prefix_the_key_and_url_already_use() -> None:
    """`OPENROUTER_API_KEY` and `OPENROUTER_BASE_URL` set the prefix a reader expects
    the model to share, and a model named that way used to be ignored in silence."""
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "k", "OPENROUTER_MODEL": "openai/gpt-5-mini"}
    )

    assert config.model == "openai/gpt-5-mini"


def test_cora_model_wins_over_the_openrouter_alias() -> None:
    config = Config.from_env(
        {
            "OPENROUTER_API_KEY": "k",
            "CORA_MODEL": "anthropic/claude",
            "OPENROUTER_MODEL": "openai/gpt-5-mini",
        }
    )

    assert config.model == "anthropic/claude"


def test_a_model_named_with_only_blanks_is_no_name_at_all() -> None:
    """A variable left blank in a `.env` reads as unset to the person who blanked it,
    so it must not outrank the alias it was written above."""
    config = Config.from_env(
        {
            "OPENROUTER_API_KEY": "k",
            "CORA_MODEL": "   ",
            "OPENROUTER_MODEL": "openai/gpt-5-mini",
        }
    )

    assert config.model == "openai/gpt-5-mini"


def test_a_model_is_taken_without_the_spaces_around_it() -> None:
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "k", "CORA_MODEL": " anthropic/claude "}
    )

    assert config.model == "anthropic/claude"


def test_several_plugins_are_read_in_the_order_they_were_named() -> None:
    config = Config.from_env(
        {
            "OPENROUTER_API_KEY": "k",
            "CORA_PLUGINS": "cora.plugins.security, cora.plugins.fitness",
        }
    )

    assert config.plugin_modules == ("cora.plugins.security", "cora.plugins.fitness")


def test_a_fresh_install_loads_no_plugin_at_all() -> None:
    """Bare cora is the default, not a thing you have to ask for: a plugin is an
    extension, so naming one is the only way to get one. Unset and set-empty therefore
    agree — there is no default set left for them to differ about."""
    empty = Config.from_env({"OPENROUTER_API_KEY": "k", "CORA_PLUGINS": ""})
    unset = Config.from_env({"OPENROUTER_API_KEY": "k"})

    assert DEFAULT_PLUGINS == ()
    assert empty.plugin_modules == ()
    assert unset.plugin_modules == ()


def test_the_memory_default_sits_beside_the_document_store() -> None:
    """Two files, one directory: whatever fixes the CWD-relative default fixes both."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert Path(config.memory_path).parent == Path(config.db_path).parent


def test_a_memory_path_blanked_rather_than_deleted_is_no_path_at_all() -> None:
    """`sqlite3.connect("")` opens a private database that is deleted with the
    connection, so a blank taken as a value loses every remembered fact in silence."""
    config = Config.from_env({"OPENROUTER_API_KEY": "k", "CORA_MEMORY_PATH": "   "})

    assert config.memory_path == DEFAULT_MEMORY_PATH


@pytest.mark.parametrize(
    ("variable", "field"),
    [
        ("CORA_DB_PATH", "db_path"),
        ("OPENROUTER_BASE_URL", "base_url"),
    ],
)
def test_no_setting_takes_a_blank_for_an_answer(variable: str, field: str) -> None:
    """The memory path is where it was found, not where it ends: a blank is not a value
    anywhere in `from_env`, so a store that opens nowhere and a client that posts
    nowhere are the same mistake."""
    blanked = Config.from_env({"OPENROUTER_API_KEY": "k", variable: "   "})
    unset = Config.from_env({"OPENROUTER_API_KEY": "k"})

    assert getattr(blanked, field) == getattr(unset, field)


def test_a_path_is_taken_without_the_spaces_around_it() -> None:
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "k", "CORA_DB_PATH": " /tmp/vectors "}
    )

    assert config.db_path == "/tmp/vectors"


def test_a_key_of_only_blanks_is_no_key_at_all() -> None:
    """The one variable with nothing to fall back on, so a blank has to stop startup:
    sent as-is it comes back a 401, and the user is told the assistant is temporarily
    unavailable instead of that their key is missing."""
    with pytest.raises(ConfigurationError) as excinfo:
        Config.from_env({"OPENROUTER_API_KEY": "   "})

    assert "OPENROUTER_API_KEY" in excinfo.value.user_message


def test_a_key_is_taken_without_the_spaces_around_it() -> None:
    """Pasting from a `.env` line brings the trailing space with it."""
    config = Config.from_env({"OPENROUTER_API_KEY": " sk-live "})

    assert config.api_key == "sk-live"


@pytest.mark.parametrize(
    "variable", ["CORA_TOP_K", "CORA_MAX_TOOL_ROUNDS", "CORA_HISTORY_TURNS"]
)
def test_a_count_of_only_blanks_reads_as_unset_rather_than_as_a_number(
    variable: str,
) -> None:
    """Loud where the paths were silent, but the same mistake: a variable blanked in a
    `.env` refused to start the app at all."""
    blanked = Config.from_env({"OPENROUTER_API_KEY": "k", variable: "   "})
    unset = Config.from_env({"OPENROUTER_API_KEY": "k"})

    assert blanked == unset


def test_from_env_reads_nothing_about_retrieval() -> None:
    """There is one way to search, so the environment that used to choose between them
    configures the same app as an environment that never mentioned it — including the
    mode that no longer exists, which is ignored rather than refused."""
    stale = Config.from_env(
        {
            "OPENROUTER_API_KEY": "key-123",
            "CORA_RETRIEVAL": "advanced",
            "CORA_FUSION_QUERIES": "6",
        }
    )

    assert stale == Config.from_env({"OPENROUTER_API_KEY": "key-123"})


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
