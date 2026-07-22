import pytest

from docchat.errors import PluginLoadError
from docchat.plugin_registry import load_plugin


def test_resolving_a_name_returns_the_module_level_plugin_bundle() -> None:
    plugin = load_plugin("fixture_plugins.valid")

    assert plugin.system_prompt == "You are a test plugin."
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
    "no_bundle",  # module lacks a PLUGIN attribute
    "wrong_type",  # PLUGIN is not a Plugin instance
    "blank_prompt",  # system_prompt is blank
    "no_tools",  # bundle provides no tools
    "duplicate_names",  # two tools share a name
    "non_callable_run",  # a tool's run is not callable
    "bad_schema",  # a tool's parameter_schema is invalid
]


@pytest.mark.parametrize("fixture", BAD_PLUGIN_FIXTURES)
def test_bad_plugin_bundle_raises_typed_error(fixture: str) -> None:
    module_path = f"fixture_plugins.{fixture}"

    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin(module_path)

    assert module_path in excinfo.value.user_message
