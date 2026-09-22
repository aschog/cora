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
    package = pathlib.Path(importlib.import_module(module).__file__ or "").parent
    (tmp_path / package.name).symlink_to(package)

    (loaded,) = load_plugins([], folder=tmp_path)

    assert loaded.module == package.name
