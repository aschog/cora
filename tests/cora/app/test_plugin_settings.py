"""What a plugin may read as its own settings, and what it may never read."""

from cora.app.config import PLUGIN_PREFIX, plugin_settings

FITNESS = "cora.plugins.fitness"
BIRDS = "acme.plugins.birds"


def test_a_plugin_reads_the_variables_named_for_it() -> None:
    settings = plugin_settings((FITNESS,), {f"{PLUGIN_PREFIX}FITNESS_UNITS": "metric"})

    assert settings == {FITNESS: {"units": "metric"}}


def test_a_plugin_reads_no_variable_named_for_another() -> None:
    settings = plugin_settings(
        (FITNESS, BIRDS),
        {
            f"{PLUGIN_PREFIX}FITNESS_UNITS": "metric",
            f"{PLUGIN_PREFIX}BIRDS_SEASON": "spring",
        },
    )

    assert settings == {FITNESS: {"units": "metric"}, BIRDS: {"season": "spring"}}


def test_a_plugin_reads_none_of_coras_own_configuration() -> None:
    """The one that would have bitten: a plugin whose module ends in `log` reading
    `CORA_LOG_PATH` would be handed the path to the user's log file. Cora's own
    variables and a plugin's live in separate namespaces."""
    settings = plugin_settings(
        ("acme.plugins.log",),
        {
            "CORA_LOG_PATH": "/home/someone/.cora/logs/cora.log",
            "CORA_DB_PATH": "/home/someone/.cora/cora.sqlite",
            "OPENROUTER_API_KEY": "sk-live-secret",
        },
    )

    assert settings == {"acme.plugins.log": {}}


def test_a_plugin_with_nothing_set_reads_nothing() -> None:
    assert plugin_settings((FITNESS,), {}) == {FITNESS: {}}
