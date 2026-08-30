import pytest

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.engine.plugin_registry import load_plugin, load_plugins


def test_loading_a_plugin_hands_back_the_module_and_its_extend() -> None:
    """Loading imports and checks the module. What the plugin contributes is registered
    later, against a host, because a host is made of an assembled app's own parts."""
    loaded = load_plugin("fixture_plugins.valid")

    assert loaded.module == "fixture_plugins.valid"
    assert callable(loaded.extend)


def test_missing_plugin_module_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.no_such_module")

    assert "fixture_plugins.no_such_module" in excinfo.value.user_message
    assert isinstance(excinfo.value.__cause__, ModuleNotFoundError)


def test_plugin_with_missing_dependency_is_reported_as_failed_import() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.missing_dependency")

    assert "failed to import" in excinfo.value.user_message
    assert "was not found" not in excinfo.value.user_message


def test_plugin_module_raising_during_import_surfaces_as_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.broken_import")

    assert "fixture_plugins.broken_import" in excinfo.value.user_message
    assert isinstance(excinfo.value.__cause__, RuntimeError)


NOT_A_PLUGIN = [
    ("no_extend", "defines no extend"),
    ("wrong_type", "extend is not callable"),
]


@pytest.mark.parametrize(("fixture", "reason"), NOT_A_PLUGIN)
def test_a_module_that_is_not_a_plugin_is_refused_by_name(
    fixture: str, reason: str
) -> None:
    module_path = f"fixture_plugins.{fixture}"

    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin(module_path)

    assert module_path in excinfo.value.user_message
    assert reason in excinfo.value.user_message


def test_one_bad_module_in_a_list_names_that_module_not_the_list() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugins(
            [
                "fixture_plugins.valid",
                "fixture_plugins.no_such_module",
                "fixture_plugins.rules_only",
            ]
        )

    assert "fixture_plugins.no_such_module" in excinfo.value.user_message
    assert "fixture_plugins.valid" not in excinfo.value.user_message


def test_one_module_named_twice_is_a_config_error() -> None:
    """Otherwise a tool-name collision reads as a plugin colliding with itself, and the
    user is told nothing about what they actually typed."""
    with pytest.raises(ConfigurationError) as excinfo:
        load_plugins(["fixture_plugins.valid", "fixture_plugins.valid"])

    assert "fixture_plugins.valid" in excinfo.value.user_message
    assert "twice" in excinfo.value.user_message


def test_two_modules_named_alike_at_the_end_are_refused() -> None:
    """A name is what tells two plugins apart: it heads their sections of the brief and
    it names their settings. Two `fitness` plugins would share both."""
    with pytest.raises(ConfigurationError) as refused:
        load_plugins(["acme.plugins.valid", "fixture_plugins.valid"])

    assert "acme.plugins.valid" in refused.value.user_message
    assert "fixture_plugins.valid" in refused.value.user_message
    assert "Rename one" in refused.value.user_message
