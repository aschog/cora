from fixture_plugins import make_plugin, make_tool

PLUGIN = make_plugin(tools=(make_tool("one"), make_tool("one"), make_tool("two")))
