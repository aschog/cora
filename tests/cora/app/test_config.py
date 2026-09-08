from pathlib import Path

import pytest

from cora.app.config import (
    DEFAULT_MEMORY_PATH,
    DEFAULT_MODEL,
    DEFAULT_PLUGINS,
    DEFAULT_PLUGINS_PATH,
    DEFAULT_SCOPES,
    Config,
)
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
            "CORA_MAX_OUTPUT_TOKENS": "500",
            "CORA_REQUEST_TIMEOUT": "45",
            "CORA_REASONING_EFFORT": "high",
            "CORA_LOG_PATH": "/tmp/cora.log",
            "CORA_DB_PATH": "/tmp/vectors",
            "CORA_MEMORY_PATH": "/tmp/memory.sqlite",
            "CORA_DOCUMENTS_PATH": "/tmp/documents",
            "CORA_CONVERSATIONS_PATH": "/tmp/conversations.sqlite",
            "CORA_OUTPUT_PATH": "/tmp/kept",
            "CORA_SCOPES": " fitness , cooking ,",
            "CORA_PLUGINS_PATH": "/tmp/dropped",
        }
    )

    assert config == Config(
        api_key="key-123",
        model="anthropic/claude",
        base_url="https://example/api",
        plugin_modules=("cora.plugins.custom",),
        scopes=("fitness", "cooking"),
        top_k=7,
        max_tool_rounds=3,
        history_turns=9,
        max_output_tokens=500,
        request_timeout_seconds=45,
        reasoning_effort="high",
        log_path="/tmp/cora.log",
        db_path="/tmp/vectors",
        memory_path="/tmp/memory.sqlite",
        documents_path="/tmp/documents",
        conversations_path="/tmp/conversations.sqlite",
        output_path="/tmp/kept",
        plugins_path="/tmp/dropped",
    )


def test_from_env_applies_defaults_for_optional_fields() -> None:
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.model
    assert config.base_url
    assert config.plugin_modules == DEFAULT_PLUGINS
    assert config.scopes == DEFAULT_SCOPES
    assert config.top_k > 0
    assert config.max_tool_rounds > 0
    assert config.history_turns > 0
    assert config.db_path
    assert config.memory_path
    assert config.plugins_path == DEFAULT_PLUGINS_PATH


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
    assert Path(config.documents_path).parent == Path(config.db_path).parent
    assert Path(config.conversations_path).parent == Path(config.db_path).parent


def test_the_index_default_is_a_file_rather_than_a_directory() -> None:
    """The index is one SQLite file cora opens itself, so the default names a file —
    a deployment pointing this at a directory is pointing it at nothing."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert Path(config.db_path).suffix == ".sqlite"
    assert Path(config.db_path).parent == Path(".cora")


def test_the_output_location_is_not_under_the_stores_cora_keeps_for_itself() -> None:
    """What an effect produces is the user's to keep, so it does not land among the
    indexes and databases cora would delete to start clean."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.output_path
    assert Path(config.output_path).parent != Path(config.db_path).parent


def test_a_memory_path_blanked_rather_than_deleted_is_no_path_at_all() -> None:
    """`sqlite3.connect("")` opens a private database that is deleted with the
    connection, so a blank taken as a value loses every remembered fact in silence."""
    config = Config.from_env({"OPENROUTER_API_KEY": "k", "CORA_MEMORY_PATH": "   "})

    assert config.memory_path == DEFAULT_MEMORY_PATH


@pytest.mark.parametrize(
    ("variable", "field"),
    [
        ("CORA_DB_PATH", "db_path"),
        ("CORA_DOCUMENTS_PATH", "documents_path"),
        ("CORA_CONVERSATIONS_PATH", "conversations_path"),
        ("CORA_OUTPUT_PATH", "output_path"),
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
    "variable",
    [
        "CORA_TOP_K",
        "CORA_MAX_TOOL_ROUNDS",
        "CORA_HISTORY_TURNS",
        "CORA_MAX_OUTPUT_TOKENS",
        "CORA_REQUEST_TIMEOUT",
    ],
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
    "var",
    [
        "CORA_TOP_K",
        "CORA_MAX_TOOL_ROUNDS",
        "CORA_HISTORY_TURNS",
        "CORA_MAX_OUTPUT_TOKENS",
        "CORA_REQUEST_TIMEOUT",
    ],
)
def test_from_env_non_integer_value_raises_configuration_error(var: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", var: "lots"})


@pytest.mark.parametrize(
    "var",
    [
        "CORA_TOP_K",
        "CORA_MAX_TOOL_ROUNDS",
        "CORA_HISTORY_TURNS",
        "CORA_MAX_OUTPUT_TOKENS",
        "CORA_REQUEST_TIMEOUT",
    ],
)
def test_from_env_negative_value_raises_configuration_error(var: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", var: "-1"})


@pytest.mark.parametrize(
    "var",
    [
        "CORA_TOP_K",
        "CORA_MAX_TOOL_ROUNDS",
        "CORA_MAX_OUTPUT_TOKENS",
        "CORA_REQUEST_TIMEOUT",
    ],
)
def test_from_env_zero_raises_where_one_is_the_lowest_useful_value(var: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", var: "0"})


def test_from_env_allows_zero_history_turns_to_switch_memory_off() -> None:
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "key-123", "CORA_HISTORY_TURNS": "0"}
    )

    assert config.history_turns == 0


def test_the_default_output_budget_fits_a_reasoning_model_thinking_and_answering() -> (
    None
):
    """Measured against `openai/gpt-5-mini`: a training-plan answer spent about 1200
    tokens reasoning before its first word and some 3200 in all. A budget that fits only
    the thinking returns `finish_reason="length"` every time, so no retry can help."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.max_output_tokens >= 4096


def test_the_default_deadline_outlasts_a_reasoning_models_slowest_answer() -> None:
    """Measured against `openai/gpt-5-mini`: the same training-plan answer took 37-56
    seconds to arrive. A deadline inside that range trades the truncated answer for a
    timed-out one, which is the same failed turn wearing another message."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.request_timeout_seconds >= 90


def test_the_default_effort_keeps_the_citations_and_the_least_time() -> None:
    """Measured against `openai/gpt-5-mini` on one question: `medium`, the provider's
    own default, spent 32-61s a turn and `low` 22-25s, and both searched and
    cited them. `high` is the setting to leave alone — it spent an entire 8192-token
    budget thinking and returned no answer at all."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.reasoning_effort == "low"


@pytest.mark.parametrize("raw", ["lots", "LOW", "none", "0"])
def test_an_effort_no_provider_defines_is_refused_at_startup(raw: str) -> None:
    """Sent instead of refused it comes back as a provider error mid-question, by which
    time the user is the one reading it."""
    with pytest.raises(ConfigurationError):
        Config.from_env({"OPENROUTER_API_KEY": "key-123", "CORA_REASONING_EFFORT": raw})


@pytest.mark.parametrize("raw", ["low", "medium", "high"])
def test_every_effort_the_provider_defines_is_accepted(raw: str) -> None:
    config = Config.from_env(
        {"OPENROUTER_API_KEY": "key-123", "CORA_REASONING_EFFORT": raw}
    )

    assert config.reasoning_effort == raw


def test_the_log_path_is_a_setting_like_every_other_path() -> None:
    """The last store a deployment could not place: the debug log went where the module
    said, so a run from anywhere but the working directory wrote its trace somewhere the
    deployment never chose."""
    config = Config.from_env({"OPENROUTER_API_KEY": "key-123"})

    assert config.log_path
    blanked = Config.from_env({"OPENROUTER_API_KEY": "key-123", "CORA_LOG_PATH": "  "})
    assert blanked.log_path == config.log_path, "a blank reads as unset, as paths do"


def test_the_default_model_is_the_one_a_deployment_gets_for_naming_none() -> None:
    """The default reaches anyone who runs cora without naming a model, so the name is
    pinned here: a change to it is a deployment answering from a model at a cost and a
    latency nothing promised."""
    assert DEFAULT_MODEL == "openai/gpt-4o-mini"
