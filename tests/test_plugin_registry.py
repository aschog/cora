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


def test_plugin_module_raising_during_import_surfaces_as_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.broken_import")

    assert "fixture_plugins.broken_import" in excinfo.value.user_message
    assert isinstance(excinfo.value.__cause__, RuntimeError)


def test_module_lacking_a_plugin_attribute_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.no_bundle")

    assert "fixture_plugins.no_bundle" in excinfo.value.user_message


def test_plugin_attribute_that_is_not_a_plugin_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.wrong_type")

    assert "fixture_plugins.wrong_type" in excinfo.value.user_message


def test_bundle_with_blank_system_prompt_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.blank_prompt")

    assert "fixture_plugins.blank_prompt" in excinfo.value.user_message


def test_bundle_with_no_tools_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.no_tools")

    assert "fixture_plugins.no_tools" in excinfo.value.user_message


def test_bundle_with_duplicate_tool_names_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.duplicate_names")

    assert "fixture_plugins.duplicate_names" in excinfo.value.user_message
