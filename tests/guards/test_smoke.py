import pathlib
from importlib.metadata import version
from types import ModuleType

import cora
import cora.adapters
import cora.app
import cora.domain
import cora.engine
import cora.frontends.react
import cora.plugins.fitness
import cora.plugins.security
import cora.ports
import workspace

DISTRIBUTIONS = tuple(workspace.distribution(member) for member in workspace.members())


def _carrier(module: ModuleType) -> str:
    path = pathlib.Path(str(module.__file__))
    src = next(parent for parent in path.parents if parent.name == "src")
    return workspace.location(src.parent)


def test_the_layers_share_one_namespace_across_its_distributions() -> None:
    assert not getattr(cora, "__file__", None)
    assert {version(name) for name in DISTRIBUTIONS} == {"0.1.0"}


def test_each_layer_is_carried_by_the_member_that_ships_it() -> None:
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
            cora.frontends.react,
        )
    }

    assert carriers == {
        "cora.domain": ".",
        "cora.ports": ".",
        "cora.engine": ".",
        "cora.adapters": ".",
        "cora.app": ".",
        "cora.plugins.fitness": "plugins/fitness",
        "cora.plugins.security": "plugins/security",
        "cora.frontends.react": "frontends/react",
    }
