import pytest

from cora.domain.errors import PluginLoadError
from cora.engine.plugin_registry import load_plugin


def test_resolving_a_name_returns_the_module_level_plugin_bundle() -> None:
    plugin = load_plugin("fixture_plugins.valid")

    assert plugin.instructions == "You are a test plugin."
    assert [tool.name for tool in plugin.tools] == ["one", "two", "three"]


def test_a_bundle_of_rules_alone_loads() -> None:
    """What makes a guard plugin possible: it offers the model nothing and only
    turns input down."""
    plugin = load_plugin("fixture_plugins.rules_only")

    assert plugin.tools == ()
    assert len(plugin.validation_rules) == 1
    assert plugin.instructions == ""


def test_a_bundle_of_tools_alone_loads() -> None:
    plugin = load_plugin("fixture_plugins.tools_only")

    assert plugin.instructions == ""
    assert [tool.name for tool in plugin.tools] == ["one", "two", "three"]


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


BAD_PLUGIN_FIXTURES = [
    ("no_bundle", "defines no PLUGIN"),
    ("wrong_type", "not a Plugin bundle"),
    ("blank_name", "name is blank"),
    ("duplicate_names", "share the same name"),
    ("non_callable_run", "no callable run"),
    ("bad_schema", "invalid parameter schema"),
]


@pytest.mark.parametrize(("fixture", "reason"), BAD_PLUGIN_FIXTURES)
def test_bad_plugin_bundle_raises_typed_error_naming_the_failure(
    fixture: str, reason: str
) -> None:
    module_path = f"fixture_plugins.{fixture}"

    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin(module_path)

    assert module_path in excinfo.value.user_message
    assert reason in excinfo.value.user_message
