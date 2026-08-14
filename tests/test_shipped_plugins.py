"""Every plugin cora ships, through the loader that will really load it.

Here rather than in a plugin's own suite, which asserts what the bundle holds and needs
no loader to do it. Whether the registry accepts what a plugin declares is its own
subject, and it is the same question for every plugin — asking it once, over the bundles
found in the namespace, covers the next plugin as well as these two.
"""

import pkgutil

import pytest

import cora.plugins
from cora.engine.plugin_registry import load_plugin
from cora.ports.plugin import Plugin


def _shipped_modules() -> list[str]:
    """Found through the namespace rather than the manifests: `cora.plugins` spans the
    guard the app ships and the domain that ships as a wheel of its own, and asking the
    installed namespace covers both without knowing which is which."""
    return sorted(
        f"cora.plugins.{found.name}"
        for found in pkgutil.iter_modules(cora.plugins.__path__)
    )


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_bundle_loads_through_the_registry(module: str) -> None:
    plugin = load_plugin(module)

    assert isinstance(plugin, Plugin)
    assert plugin.name.strip()
