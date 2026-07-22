from docchat.plugin_registry import load_plugin


def test_resolving_a_name_returns_the_module_level_plugin_bundle() -> None:
    plugin = load_plugin("fixture_plugins.valid")

    assert plugin.system_prompt == "You are a test plugin."
    assert [tool.name for tool in plugin.tools] == ["one", "two", "three"]
