from pathlib import Path

import pytest

from cora.app.config import (
    DEFAULT_DB_PATH,
    DEFAULT_MODEL,
    DEFAULT_PLUGINS,
    DEFAULT_PLUGINS_PATH,
    DEFAULT_SCOPES,
    Config,
)
from cora.domain.errors import ConfigurationError

KEY = {"OPENROUTER_API_KEY": "k"}
COUNTS = (
    "CORA_TOP_K",
    "CORA_MAX_TOOL_ROUNDS",
    "CORA_HISTORY_TURNS",
    "CORA_MAX_OUTPUT_TOKENS",
    "CORA_REQUEST_TIMEOUT",
)
# Every setting whose value is a string, and the field it lands in. One table: a blank
# is not a value anywhere in `from_env`, so a store that opens nowhere and a client that
# posts nowhere are the same mistake, and neither may outrank an unset variable.
TEXT = (
    ("CORA_DB_PATH", "db_path"),
    ("CORA_DOCUMENTS_PATH", "documents_path"),
    ("CORA_OUTPUT_PATH", "output_path"),
    ("CORA_LOG_PATH", "log_path"),
    ("OPENROUTER_BASE_URL", "base_url"),
    ("CORA_MODEL", "model"),
)


def default() -> Config:
    return Config.from_env(KEY)


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
            "CORA_DB_PATH": "/tmp/cora.sqlite",
            "CORA_DOCUMENTS_PATH": "/tmp/documents",
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
        db_path="/tmp/cora.sqlite",
        documents_path="/tmp/documents",
        output_path="/tmp/kept",
        plugins_path="/tmp/dropped",
    )


def test_from_env_applies_defaults_for_optional_fields() -> None:
    """Bare cora is the default, not a thing you have to ask for, so `CORA_PLUGINS`
    unset and set-empty agree: there is no default set left for them to differ about."""
    config = default()

    assert DEFAULT_PLUGINS == () and config.plugin_modules == ()
    assert Config.from_env({**KEY, "CORA_PLUGINS": ""}).plugin_modules == ()
    assert config.scopes == DEFAULT_SCOPES
    assert config.plugins_path == DEFAULT_PLUGINS_PATH
    assert config.model and config.base_url and config.log_path
    assert config.top_k > 0 and config.max_tool_rounds > 0 and config.history_turns > 0


@pytest.mark.parametrize(("variable", "field"), TEXT)
def test_a_blank_is_no_value_and_the_spaces_around_one_are_not_part_of_it(
    variable: str, field: str
) -> None:
    """A variable left blank in a `.env` reads as unset to the person who blanked it —
    `sqlite3.connect("")` opens a database deleted with the connection — and pasting
    from a `.env` line brings the trailing space with it.
    """
    blanked = Config.from_env({**KEY, variable: "   "})
    spaced = Config.from_env({**KEY, variable: " /tmp/somewhere "})

    assert getattr(blanked, field) == getattr(default(), field)
    assert getattr(spaced, field) == "/tmp/somewhere"


@pytest.mark.parametrize("variable", COUNTS)
def test_a_count_of_only_blanks_reads_as_unset_rather_than_as_a_number(
    variable: str,
) -> None:
    """Loud where the paths were silent, but the same mistake: a variable blanked in a
    `.env` refused to start the app at all."""
    assert Config.from_env({**KEY, variable: "   "}) == default()


def test_the_key_is_the_one_setting_with_nothing_to_fall_back_on() -> None:
    """Sent as-is a blank comes back a 401, and the user is told the assistant is
    temporarily unavailable instead of that their key is missing."""
    with pytest.raises(ConfigurationError) as excinfo:
        Config.from_env({"OPENROUTER_API_KEY": "   "})
    assert "OPENROUTER_API_KEY" in excinfo.value.user_message

    with pytest.raises(ConfigurationError):
        Config.from_env({})
    assert Config.from_env({"OPENROUTER_API_KEY": " sk-live "}).api_key == "sk-live"


def test_the_model_may_be_named_with_the_prefix_the_key_and_url_already_use() -> None:
    """`OPENROUTER_API_KEY` and `OPENROUTER_BASE_URL` set the prefix a reader expects
    the model to share, and a model named that way used to be ignored in silence. Cora's
    own name wins where both are set, and a blank one does not outrank the alias."""
    alias = {"OPENROUTER_MODEL": "openai/gpt-5-mini"}

    assert Config.from_env({**KEY, **alias}).model == "openai/gpt-5-mini"
    assert Config.from_env({**KEY, **alias, "CORA_MODEL": "a/b"}).model == "a/b"
    assert (
        Config.from_env({**KEY, **alias, "CORA_MODEL": " "}).model
        == alias["OPENROUTER_MODEL"]
    )


def test_several_plugins_are_read_in_the_order_they_were_named() -> None:
    named = Config.from_env({**KEY, "CORA_PLUGINS": "cora.a, cora.b"})

    assert named.plugin_modules == ("cora.a", "cora.b")


@pytest.mark.parametrize(
    "stale",
    [
        # What the facts and the turns used to be moved by, before one file held both,
        # and what used to choose between two ways of searching.
        "CORA_MEMORY_PATH",
        "CORA_CONVERSATIONS_PATH",
        "CORA_RETRIEVAL",
        "CORA_FUSION_QUERIES",
    ],
)
def test_a_retired_variable_is_read_by_nothing(stale: str) -> None:
    """Set by a deployment that has not caught up, and it changes nothing rather than
    quietly sending half the stores somewhere else."""
    assert Config.from_env({**KEY, stale: "elsewhere"}) == default()
    assert not hasattr(default(), "memory_path")


@pytest.mark.parametrize("raw", ["lots", "-1"])
@pytest.mark.parametrize("variable", COUNTS)
def test_a_count_that_is_not_one_is_refused_at_startup(variable: str, raw: str) -> None:
    with pytest.raises(ConfigurationError):
        Config.from_env({**KEY, variable: raw})


@pytest.mark.parametrize("variable", [v for v in COUNTS if v != "CORA_HISTORY_TURNS"])
def test_zero_is_refused_where_one_is_the_lowest_useful_value(variable: str) -> None:
    """History alone takes it: zero turns is memory switched off, not a broken
    setting."""
    with pytest.raises(ConfigurationError):
        Config.from_env({**KEY, variable: "0"})

    assert Config.from_env({**KEY, "CORA_HISTORY_TURNS": "0"}).history_turns == 0


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "True"])
def test_from_env_turns_debug_on_for_truthy_flags(raw: str) -> None:
    assert Config.from_env({**KEY, "CORA_DEBUG": raw}).debug is True


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", ""])
def test_from_env_keeps_debug_off_for_falsy_flags(raw: str) -> None:
    assert Config.from_env({**KEY, "CORA_DEBUG": raw}).debug is False
    assert default().debug is False


@pytest.mark.parametrize("raw", ["lots", "LOW", "none", "0"])
def test_an_effort_no_provider_defines_is_refused_at_startup(raw: str) -> None:
    """Sent instead of refused it comes back as a provider error mid-question, by which
    time the user is the one reading it."""
    with pytest.raises(ConfigurationError):
        Config.from_env({**KEY, "CORA_REASONING_EFFORT": raw})


@pytest.mark.parametrize("raw", ["low", "medium", "high"])
def test_every_effort_the_provider_defines_is_accepted(raw: str) -> None:
    assert (
        Config.from_env({**KEY, "CORA_REASONING_EFFORT": raw}).reasoning_effort == raw
    )


def test_the_defaults_a_deployment_gets_for_naming_nothing() -> None:
    """Measured against `openai/gpt-5-mini`: a training-plan answer spent about 1200
    tokens reasoning before its first word and some 3200 in all, and took 37-56 seconds
    to arrive — a budget that fits only the thinking returns `finish_reason="length"`
    every time, and a deadline inside that range trades the truncated answer for a
    timed-out one. `low` effort spent 22-25s a turn against `medium`'s 32-61s and cited
    just as well. `high` spent a whole 8192-token budget thinking and answered nothing.
    The model name is pinned because a change to it is every deployment that named none
    answering at another cost and another latency.
    """
    config = default()

    assert DEFAULT_MODEL == "openai/gpt-4o-mini"
    assert config.max_output_tokens >= 4096
    assert config.request_timeout_seconds >= 90
    assert config.reasoning_effort == "low"


def test_everything_cora_keeps_for_itself_is_one_file_and_the_output_is_not() -> None:
    """The passages, the facts, the turns and the checkpoints are in it, so the default
    names a file and not a directory — and what an effect produces is the user's to
    keep, so it does not land among the stores cora would delete to start clean."""
    config = default()

    assert Path(config.db_path) == Path(DEFAULT_DB_PATH) == Path(".cora/cora.sqlite")
    assert Path(config.documents_path).parent == Path(config.db_path).parent
    assert Path(config.output_path).parent != Path(config.db_path).parent
