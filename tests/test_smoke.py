"""Smoke test proving the package wiring and test runner work."""

import pathlib
from importlib.metadata import version
from types import ModuleType

import cora
import cora.adapters
import cora.app
import cora.core
import cora.plugins.fitness

DISTRIBUTIONS = ("cora-core", "cora-adapters", "cora-fitness", "cora-app")


def _carrier(module: ModuleType) -> str:
    """Which workspace member a layer was installed from, read off the path rather than
    the nesting depth — `cora.plugins.fitness` sits one level deeper than the rest. The
    directory is named for the layer; the distribution it builds keeps the `cora-`
    prefix, and `test_packaging.py` pins that mapping."""
    path = pathlib.Path(str(module.__file__))
    src = next(parent for parent in path.parents if parent.name == "src")
    return src.parent.name


def test_the_layers_share_one_namespace_across_four_distributions() -> None:
    """`cora` is a namespace, not a package: each layer ships separately and they meet
    at import time. A stray `cora/__init__.py` in any of them would claim the name for
    one distribution and hide the others."""
    assert not getattr(cora, "__file__", None)
    assert {version(name) for name in DISTRIBUTIONS} == {"0.1.0"}


def test_each_layer_is_carried_by_its_own_workspace_member() -> None:
    carriers = {
        module.__name__: _carrier(module)
        for module in (cora.core, cora.adapters, cora.app, cora.plugins.fitness)
    }

    assert carriers == {
        "cora.core": "core",
        "cora.adapters": "adapters",
        "cora.app": "app",
        "cora.plugins.fitness": "fitness",
    }
