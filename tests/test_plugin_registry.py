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
