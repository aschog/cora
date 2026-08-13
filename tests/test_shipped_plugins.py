"""Every plugin cora ships, through the loader that will really load it.

Here rather than in a plugin's own suite, which asserts what the bundle holds and needs
no loader to do it. Whether the registry accepts what a plugin declares is its own
subject, and it is the same question for every plugin — asking it once, over the members
found in the tree, covers the next plugin as well as these two.
"""

import pathlib

import pytest
import tomllib

from cora.engine.plugin_registry import load_plugin
from cora.ports.plugin import Plugin

PACKAGES = pathlib.Path(__file__).resolve().parent.parent / "packages"


def _shipped_modules() -> list[str]:
    return sorted(
        tomllib.loads((path / "pyproject.toml").read_text())["tool"]["uv"][
            "build-backend"
        ]["module-name"]
        for path in (PACKAGES / "plugins").iterdir()
        if (path / "pyproject.toml").is_file()
    )


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_bundle_loads_through_the_registry(module: str) -> None:
    plugin = load_plugin(module)

    assert isinstance(plugin, Plugin)
    assert plugin.name.strip()
