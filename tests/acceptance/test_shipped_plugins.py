"""Every plugin cora ships, through the loader that will really load it.

Here rather than in a plugin's own suite, which asserts what the plugin registers and
needs no loader to do it. Whether a module loads at all is its own subject, and it is
the same question for every plugin — asking it once, over the modules found in the
namespace, covers the next plugin as well as these two.
"""

import importlib
import pathlib
import pkgutil

import pytest

import cora.plugins
from cora.engine.plugin_registry import load_plugin, load_plugins
from cora.ports.host import Extension


def _shipped_modules() -> list[str]:
    return sorted(
        f"cora.plugins.{found.name}"
        for found in pkgutil.iter_modules(cora.plugins.__path__)
    )


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_plugin_loads_through_the_registry(module: str) -> None:
    loaded = load_plugin(module)

    assert isinstance(loaded, Extension)
    assert loaded.module == module


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_plugin_also_loads_as_a_drop_in(
    module: str, tmp_path: pathlib.Path
) -> None:
    """Shipped in the monorepo, written independent: each package must load through
    the folder too, exactly as a deployment that never installed it would load it."""
    package = pathlib.Path(importlib.import_module(module).__file__ or "").parent
    (tmp_path / package.name).symlink_to(package)

    (loaded,) = load_plugins([], folder=tmp_path)

    assert loaded.module == package.name
