"""Smoke test proving the package wiring and test runner work."""

import pathlib
from importlib.metadata import version
from types import ModuleType

import cora
import cora.adapters
import cora.app
import cora.domain
import cora.engine
import cora.frontends.streamlit
import cora.plugins.fitness
import cora.plugins.security
import cora.ports
import workspace

DISTRIBUTIONS = tuple(workspace.distribution(member) for member in workspace.members())
"""Found, not listed: a distribution added to the workspace and forgotten here would
otherwise go unversioned and unimported by every test in this file."""


def _carrier(module: ModuleType) -> str:
    """Which workspace member a layer was installed from, read off the path rather than
    the nesting depth — `cora.plugins.fitness` sits two levels deeper than the rest.
    `test_packaging.py` pins what each member is called as a distribution."""
    path = pathlib.Path(str(module.__file__))
    src = next(parent for parent in path.parents if parent.name == "src")
    return workspace.location(src.parent)


def test_the_layers_share_one_namespace_across_its_distributions() -> None:
    """`cora` is a namespace, not a package: each layer ships separately and they meet
    at import time. A stray `cora/__init__.py` in any of them would claim the name for
    one distribution and hide the others."""
    assert not getattr(cora, "__file__", None)
    assert {version(name) for name in DISTRIBUTIONS} == {"0.1.0"}


def test_each_layer_is_carried_by_the_member_that_ships_it() -> None:
    """Five layers and the guard ship from the app; what sits beside it is what a
    deployment may add. The mapping is the architecture as an install — it is what a
    second frontend or a second domain would extend without touching the app."""
    carriers = {
        module.__name__: _carrier(module)
        for module in (
            cora.domain,
            cora.ports,
            cora.engine,
            cora.adapters,
            cora.app,
            cora.plugins.fitness,
            cora.plugins.security,
            cora.frontends.streamlit,
        )
    }

    assert carriers == {
        "cora.domain": ".",
        "cora.ports": ".",
        "cora.engine": ".",
        "cora.adapters": ".",
        "cora.app": ".",
        "cora.plugins.security": ".",
        "cora.plugins.fitness": "plugins/fitness",
        "cora.frontends.streamlit": "frontends/streamlit",
    }
