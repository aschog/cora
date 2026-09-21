"""Every tool a shipped plugin registers is one the model can actually call.

A tool reaches the model as its `parameter_schema`, and reaches Python as
`run(**arguments)`. Nothing in between checks that the two agree, so a schema naming an
argument the function dropped is a `TypeError` the first time a model believes it — and
a function taking one the schema never names is a feature no model can ever reach.
Both have shipped here, which is why this is a guard and not a comment.
"""

import inspect
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from cora.engine.plugin_registry import load_plugin
from cora.ports.host import TOOL
from fakes import FakeFiles, FakeStore, host_for

PLUGINS = Path(__file__).resolve().parents[2] / "plugins"
SHIPPED = sorted(each.name for each in PLUGINS.iterdir() if (each / "src").is_dir())


def _tools(module: str) -> list:
    host = host_for(module, store=FakeStore(), files=FakeFiles())
    load_plugin(module).extend(host)
    return [entry.value for entry in host.registered if entry.kind == TOOL]


@pytest.mark.parametrize("plugin", SHIPPED)
def test_a_tools_schema_is_one_its_own_function_can_be_called_with(plugin: str) -> None:
    for tool in _tools(f"cora.plugins.{plugin}"):
        Draft202012Validator.check_schema(tool.parameter_schema)
        taken = inspect.signature(tool.run).parameters
        if any(p.kind is p.VAR_KEYWORD for p in taken.values()):
            continue
        named = set(tool.parameter_schema.get("properties", {}))
        assert named <= set(taken), (
            f"{plugin}.{tool.name} advertises {sorted(named - set(taken))}, "
            f"which its function cannot be called with"
        )


@pytest.mark.parametrize("plugin", SHIPPED)
def test_every_argument_a_tool_requires_is_one_it_advertises(plugin: str) -> None:
    for tool in _tools(f"cora.plugins.{plugin}"):
        named = set(tool.parameter_schema.get("properties", {}))
        assert set(tool.parameter_schema.get("required", ())) <= named, tool.name


@pytest.mark.parametrize("plugin", SHIPPED)
def test_an_argument_with_no_default_is_one_the_schema_requires(plugin: str) -> None:
    for tool in _tools(f"cora.plugins.{plugin}"):
        taken = inspect.signature(tool.run).parameters
        must = {
            name
            for name, each in taken.items()
            if each.default is inspect.Parameter.empty
            and each.kind not in (each.VAR_KEYWORD, each.VAR_POSITIONAL)
        }
        required = set(tool.parameter_schema.get("required", ()))
        assert must <= required, (
            f"{plugin}.{tool.name} must be called with {sorted(must - required)}, "
            f"which its schema does not require"
        )
