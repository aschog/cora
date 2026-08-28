import ast
import dataclasses
import importlib
import inspect
import pathlib
import pkgutil
import sys
import typing
from importlib.metadata import packages_distributions
from types import ModuleType

import pytest

import cora.adapters
import cora.app
import cora.domain
import cora.engine
import cora.frontends.react
import cora.plugins
import cora.ports
import workspace

PURE_MAY_USE = frozenset({"jsonschema"})
"""The one third party the contract and the engine may reach for. Validating a tool's
schema is a rule about what a plugin declares, not a technology the engine is bound to —
a deployment cannot swap it for a different one."""
TEST_ONLY_FRAMEWORKS = frozenset({"pytest"})


def _is_technology(module: str) -> bool:
    """Anything that is neither the standard library nor `cora` itself.

    Named by what a layer may use, never by what the manifests declare. A deny-list read
    off the manifests can only see the ten distributions someone asked for, while the
    environment holds every transitive one too — chromadb and langchain-openai bring
    `numpy`, `torch` and `openai` — and importing one of those binds a layer exactly as
    tightly. The install used to enforce this by absence, with nothing to keep in sync;
    an allow-list is the only form of the rule that inherits that property."""
    root = module.split(".")[0]
    return root != "cora" and root not in sys.stdlib_module_names


def _root(module: ModuleType) -> pathlib.Path:
    return pathlib.Path(str(module.__file__)).parent


# Every shipped layer, each asked of its module rather than of a directory: the layers
# are siblings under one `src/cora/`, and a rule that named the directory would have to
# be rewritten the day a layer ships from somewhere else — which is what `cora.plugins`
# already does.
PURE_ROOTS = (_root(cora.domain), _root(cora.ports), _root(cora.engine))
EXTENSION_POINTS = (cora.plugins, cora.frontends)
"""The two namespaces that expect contributors. Asked of the namespace rather than of a
directory: `cora.plugins` is one name over as many trees as there are plugins installed,
and a walk rooted at any one of them passes by covering none of the others."""


def _extension_roots() -> tuple[pathlib.Path, ...]:
    """Every portion of an extension point. A namespace package carries one `__path__`
    entry per distribution contributing to it, so a plugin added later is walked without
    being listed here."""
    return tuple(
        sorted(
            pathlib.Path(portion)
            for point in EXTENSION_POINTS
            for portion in point.__path__
        )
    )


LAYER_ROOTS = (
    *PURE_ROOTS,
    _root(cora.adapters),
    _root(cora.app),
    *_extension_roots(),
)
CORE_FILES = sorted(file for root in PURE_ROOTS for file in root.rglob("*.py"))
PACKAGE_FILES = sorted(file for root in LAYER_ROOTS for file in root.rglob("*.py"))
SKIPPED_TREES = frozenset({"node_modules", "__pycache__", "dist", "build"})
"""What the repository holds without having written: an installed environment, a build,
a cache. Hidden directories go with them, which is how `.venv` is excluded without
being named."""


def _repository_files() -> list[pathlib.Path]:
    """Every Python file the repository wrote — the packages, the tests, the tooling."""
    return sorted(
        path
        for path in workspace.ROOT.rglob("*.py")
        if not any(
            part in SKIPPED_TREES or part.startswith(".")
            for part in path.relative_to(workspace.ROOT).parts
        )
    )


REPOSITORY_FILES = _repository_files()

# What each layer may not reach for, and the reason it may not. One table rather than a
# test per layer: a rule added here is enforced over every file of that layer, and the
# reason travels into the failure message instead of a docstring nobody reads on the way
# to fixing it.
OUT_OF_REACH: dict[str, tuple[tuple[str, ...], str]] = {
    "the contract and the engine": (
        ("cora.adapters", "cora.plugins", "cora.app", "cora.frontends"),
        "the use cases and the slots they drive are what every outer layer depends on, "
        "so they may depend on none of them",
    ),
    "the adapters": (
        ("cora.engine", "cora.app", "cora.frontends"),
        "an adapter fills a slot and is reusable by every frontend and every "
        "version of the use cases, which it can only be if it knows the ports alone",
    ),
    "the app": (
        ("cora.frontends", "cora.plugins"),
        "the composition root is what a frontend installs, so naming a frontend would "
        "mean a command-line shell had to install a web UI to reuse the wiring; and it "
        "installs no plugin at all, which is why importing one rather than naming "
        "it in config has to stay impossible",
    ),
    "the plugins": (
        ("cora.engine", "cora.adapters", "cora.app", "cora.frontends"),
        "a plugin is data over the contract, which is what lets it ship as a wheel "
        "the engine is absent from: reaching any of these makes it a plugin only this "
        "deployment can install",
    ),
    "the frontends": (
        ("cora.adapters", "cora.plugins"),
        "a frontend shows what the app and the use cases hand it; reaching an adapter "
        "ties the UI to one technology binding, and naming a plugin ties it to one "
        "domain — both are chosen at assembly, not at the screen",
    ),
}
# Which shipped modules each rule above speaks for. The extension points are named by
# their namespace rather than by the plugins installed into it, so the next contributor
# is claimed by the same entry — and every name here is matched against `module-name` in
# the manifests, so a layer that ships without a rule is a failure, not a silence.
LAYER_MODULES: dict[str, tuple[str, ...]] = {
    "the contract and the engine": ("cora.domain", "cora.ports", "cora.engine"),
    "the adapters": ("cora.adapters",),
    "the app": ("cora.app",),
    "the plugins": ("cora.plugins",),
    "the frontends": ("cora.frontends",),
}
PLUGIN_ROOTS = tuple(root for root in _extension_roots() if root.name == "plugins")
FRONTEND_ROOTS = tuple(root for root in _extension_roots() if root.name == "frontends")
LAYER_FILES: dict[str, list[pathlib.Path]] = {
    "the contract and the engine": CORE_FILES,
    "the adapters": sorted(_root(cora.adapters).rglob("*.py")),
    "the app": sorted(_root(cora.app).rglob("*.py")),
    "the plugins": sorted(file for root in PLUGIN_ROOTS for file in root.rglob("*.py")),
    "the frontends": sorted(
        file for root in FRONTEND_ROOTS for file in root.rglob("*.py")
    ),
}
REACH_CASES = [(layer, path) for layer, files in LAYER_FILES.items() for path in files]

# Every technology each layer may import, and nothing outside it. The adapters are
# absent because binding one is what an adapter *is*, and the contract and the engine
# because `test_core_module_is_pure` holds them to something stricter — it bars the
# outer layers too. What is left is the three meant to be technology free, or nearly: a
# plugin is data over the contract, the composition root names adapters rather than
# importing what they wrap, and a frontend reaches for what it draws or serves with
# and no more.
TECHNOLOGY_ALLOWED: dict[str, frozenset[str]] = {
    "the app": frozenset(),
    "the plugins": frozenset(),
    "the frontends": frozenset(),
}
# The frontends are the one layer with more than one answer, so theirs is keyed by the
# portion a file ships in rather than by the layer. One set across both would read as
# "a frontend may import whatever any frontend imports" — which is how a widget shell
# quietly grows an HTTP server, declared in no manifest and caught by no gate.
FRONTEND_TOOLKITS: dict[str, frozenset[str]] = {
    "react": frozenset({"starlette", "uvicorn", "python_multipart"}),
}
TECHNOLOGY_CASES = [
    (layer, path) for layer in TECHNOLOGY_ALLOWED for path in LAYER_FILES[layer]
]


def _shipped_as(path: pathlib.Path) -> pathlib.Path:
    """The module path a file ships under — `cora/domain/chunk.py` — which is the same
    whichever distribution carries it."""
    src = next(parent for parent in path.parents if parent.name == "src")
    return path.relative_to(src)


def _package_parts(path: pathlib.Path) -> tuple[str, ...]:
    parts = _shipped_as(path).with_suffix("").parts
    return parts[:-1]  # drop the module name (or '__init__')


def _resolve(module: str | None, level: int, package_parts: tuple[str, ...]) -> str:
    base = package_parts[: len(package_parts) - (level - 1)]
    return ".".join([*base, module]) if module else ".".join(base)


def _imported_modules(tree: ast.Module, package_parts: tuple[str, ...]):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    yield node.module
            else:
                yield _resolve(node.module, node.level, package_parts)


def _imports_streamlit(path: pathlib.Path) -> bool:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] == "streamlit" for alias in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] == "streamlit"
        ):
            return True
    return False


def _test_only_imports(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return sorted(roots & TEST_ONLY_FRAMEWORKS)


def _technologies_bound(layer: str, path: pathlib.Path, tree: ast.Module) -> list[str]:
    """What a file imports that its own layer — and, for a frontend, its own shell —
    was never given."""
    allowed = (
        FRONTEND_TOOLKITS[_shipped_as(path).parts[2]]
        if layer == "the frontends"
        else TECHNOLOGY_ALLOWED[layer]
    )
    return sorted(
        {
            module
            for module in _imported_modules(tree, _package_parts(path))
            if _is_technology(module) and module.split(".")[0] not in allowed
        }
    )


def _is_forbidden(module: str) -> bool:
    """A technology the contract and the engine were not given, or a layer they may not
    reach for."""
    if _is_technology(module):
        return module.split(".")[0] not in PURE_MAY_USE
    return bool(_reaches_any(module, OUT_OF_REACH["the contract and the engine"][0]))


def _reaches_any(module: str, layers: tuple[str, ...]) -> bool:
    return any(module == layer or module.startswith(f"{layer}.") for layer in layers)


def test_the_pure_modules_are_discovered() -> None:
    assert len(PURE_ROOTS) == 3, "the contract and the engine span three modules"
    assert CORE_FILES, "no pure modules discovered — the walker is misconfigured"


def test_the_repository_walk_reads_the_tree_it_claims_to() -> None:
    """A rule over "every file" is only as true as the walk under it: one that returned
    nothing would assert nothing, and read as a clean bar rather than an empty one. The
    four kinds it claims are named here, and the two trees it must not read with them —
    an installed environment holds the very import the bar above forbids."""
    found = {str(path.relative_to(workspace.ROOT)) for path in REPOSITORY_FILES}

    assert "conftest.py" in found, "the root's own files"
    assert "src/cora/app/assembly.py" in found, "the packages"
    assert "tests/guards/test_architecture.py" in found, "the tests"
    assert "scripts/gen_component_map.py" in found, "the tooling"
    assert not [path for path in found if path.startswith(".")], "a hidden tree"
    assert not [path for path in found if "node_modules/" in path], "an installed tree"


def test_nothing_in_the_repository_imports_streamlit() -> None:
    """The whole tree, not the shipped layers alone: cora has one frontend, and a
    dependency nobody may reach for is only gone once the tests and the tooling have
    stopped reaching for it too."""
    reaching = sorted(
        str(path.relative_to(workspace.ROOT))
        for path in REPOSITORY_FILES
        if _imports_streamlit(path)
    )

    assert reaching == [], "\n".join(["these still import streamlit:", *reaching])


@pytest.mark.parametrize("path", PACKAGE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_no_test_only_framework_is_shipped(path: pathlib.Path) -> None:
    leaked = _test_only_imports(path)
    assert not leaked, f"{_shipped_as(path)} imports test-only frameworks: {leaked}"


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_no_reference_domain_word_reaches_the_contract_or_the_engine(
    path: pathlib.Path,
) -> None:
    """Domain-agnostic is a claim about words as much as imports: the plugin supplies
    the topic, so the reference domain's name has no business in the layers every other
    domain reuses. Nothing under `src/` names it at all now that the default plugin set
    is empty — a deployment says which domain it ships, in `CORA_PLUGINS`."""
    assert "fitness" not in path.read_text().lower(), (
        f"{_shipped_as(path)} names the reference domain"
    )


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_core_module_is_pure(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text())
    modules = _imported_modules(tree, _package_parts(path))
    forbidden = sorted({m for m in modules if _is_forbidden(m)})
    assert not forbidden, f"{_shipped_as(path)} imports forbidden modules: {forbidden}"


def _reaches(
    tree: ast.Module, package_parts: tuple[str, ...], layers: tuple[str, ...]
) -> list[str]:
    modules = _imported_modules(tree, package_parts)
    return sorted({module for module in modules if _reaches_any(module, layers)})


def test_every_layer_with_a_rule_has_files_to_apply_it_to() -> None:
    """Four tables keyed on the same layers, so a layer named in one and forgotten in
    another is the way this goes wrong: a rule with no modules claimed is never matched
    against a manifest, and modules with no files are never walked."""
    assert OUT_OF_REACH.keys() == LAYER_FILES.keys() == LAYER_MODULES.keys()
    assert all(LAYER_FILES[layer] for layer in OUT_OF_REACH)


def _shipped_modules() -> list[tuple[pathlib.Path, str]]:
    """Every module the workspace ships, as (directory, dotted name), read off the
    manifests and the tree. Deliberately not asked of the installed environment: a
    member outside the dev group ships modules all the same, and asking what is imported
    would make it invisible to exactly the tests meant to cover it."""
    return [
        (member / "src" / pathlib.Path(*module.split(".")), module)
        for member in workspace.members()
        for module in workspace.modules(member)
    ]


def _claiming_layer(module: str) -> str | None:
    return next(
        (
            layer
            for layer, claimed in LAYER_MODULES.items()
            for name in claimed
            if module == name or module.startswith(f"{name}.")
        ),
        None,
    )


def test_every_shipped_module_falls_under_a_layer_rule() -> None:
    """The other direction, and the one that can actually go wrong: the rules above are
    keyed on layers someone wrote down, so a sixth module added to `module-name` ships
    with no rule at all and every test here still passes. Asserted against the manifests
    so that adding a layer forces a decision about what it may reach, rather than
    granting it silence."""
    unclaimed = sorted(
        module for _, module in _shipped_modules() if _claiming_layer(module) is None
    )

    assert unclaimed == []


def test_every_shipped_module_is_reached_by_the_walk() -> None:
    """Two discoveries compared, not one restated: the rules are applied to files found
    through the installed namespaces, while `module-name` is a fact of the tree. A
    workspace member nobody added to the dev group is a module the walk never visits, so
    its rule is written and never applied — which reads just like a rule that passes."""
    unwalked = sorted(
        module
        for directory, module in _shipped_modules()
        if not any(directory.is_relative_to(root) for root in LAYER_ROOTS)
    )

    assert unwalked == []


@pytest.mark.parametrize(
    ("layer", "path"),
    REACH_CASES,
    ids=lambda value: (
        str(_shipped_as(value))
        if isinstance(value, pathlib.Path)
        else value.replace(" ", "-")
    ),
)
def test_a_layer_reaches_no_further_than_its_rule(
    layer: str, path: pathlib.Path
) -> None:
    layers, because = OUT_OF_REACH[layer]
    reached = _reaches(ast.parse(path.read_text()), _package_parts(path), layers)
    assert not reached, f"{_shipped_as(path)} reaches {reached}: {because}"


@pytest.mark.parametrize(
    ("layer", "path"),
    TECHNOLOGY_CASES,
    ids=lambda value: (
        str(_shipped_as(value))
        if isinstance(value, pathlib.Path)
        else value.replace(" ", "-")
    ),
)
def test_a_layer_binds_no_technology_it_was_not_given(
    layer: str, path: pathlib.Path
) -> None:
    """The property the install used to carry: a plugin shipped as a wheel the engine
    was absent from could not import Chroma, because Chroma was not there. One
    distribution later it is there, and only this says so."""
    bound = _technologies_bound(layer, path, ast.parse(path.read_text()))
    assert not bound, (
        f"{_shipped_as(path)} imports {bound}: {layer} is wired to a technology by "
        "the composition root, never by importing one"
    )


def test_every_layer_that_may_bind_nothing_has_files_to_say_it_of() -> None:
    assert TECHNOLOGY_ALLOWED.keys() <= LAYER_FILES.keys()
    assert all(LAYER_FILES[layer] for layer in TECHNOLOGY_ALLOWED)


def test_every_frontend_declares_the_toolkit_it_draws_or_serves_with() -> None:
    """A shell added without an entry inherits nothing — it would be allowed no
    technology at all and fail loudly, rather than inheriting the other shells'."""
    shipped = {_shipped_as(path).parts[2] for path in LAYER_FILES["the frontends"]}

    assert shipped == FRONTEND_TOOLKITS.keys()


def test_a_frontend_may_not_reach_for_a_toolkit_it_was_not_given(
    tmp_path: pathlib.Path,
) -> None:
    """The rule the map states, made false-able: a frontend reaching for a technology
    its own entry does not name is exactly as wrong as the engine importing one. With
    one frontend left the neighbour it would borrow from is hypothetical, so what is
    planted is the reach rather than the second shell."""
    drawn = ast.parse("import streamlit\n")
    served = ast.parse("import starlette.applications\n")
    http = _planted(tmp_path, "react", "api.py")

    assert _technologies_bound("the frontends", http, drawn) == ["streamlit"]
    assert _technologies_bound("the frontends", http, served) == []


def _planted(root: pathlib.Path, frontend: str, name: str) -> pathlib.Path:
    where = root / "src" / "cora" / "frontends" / frontend
    where.mkdir(parents=True, exist_ok=True)
    return where / name


def test_the_walkers_catch_a_planted_violation(tmp_path: pathlib.Path) -> None:
    """One rogue module where eight self-tests of the detectors used to be. What it
    proves is that the walks above are not vacuous: they pass by finding nothing, and a
    broken detector is indistinguishable from clean code. Those eight are also what
    rotted — three passed a `("cora", "core", "services")` package tuple naming a
    directory gone for two commits, so they could not have failed."""
    rogue = tmp_path / "rogue.py"
    rogue.write_text(
        "import streamlit as st\n"
        "import pypdf\n"
        "from langgraph.graph import StateGraph\n"
        "from pytest import fixture\n"
        "from cora.app.config import Config\n"
        "from ..adapters import chroma_retriever\n"
    )
    tree = ast.parse(rogue.read_text())

    assert _imports_streamlit(rogue)
    assert _test_only_imports(rogue) == ["pytest"]

    reached = set(_imported_modules(tree, ("cora", "engine")))
    assert "cora.adapters" in reached, (
        "a relative import out of the layer went unresolved"
    )
    assert {
        "streamlit",
        "pypdf",
        "langgraph.graph",
        "cora.app.config",
        "cora.adapters",
    } <= {module for module in reached if _is_forbidden(module)}

    outward, _ = OUT_OF_REACH["the adapters"]
    assert _reaches(tree, ("cora", "adapters"), outward) == ["cora.app.config"]


def test_a_technology_no_manifest_declares_is_still_out_of_reach(
    tmp_path: pathlib.Path,
) -> None:
    """The install used to enforce this by absence: a layer could not import what was
    not installed, and nothing had to be named. One distribution later everything is
    installed, and a rule listing what the manifests declare sees only those — while
    `openai`, `torch` and `numpy` are all present, dragged in by chromadb and
    langchain-openai, and would bind the engine exactly as tightly."""
    rogue = tmp_path / "rogue.py"
    rogue.write_text("import openai\nimport torch\nimport numpy as np\n")
    tree = ast.parse(rogue.read_text())

    bound = {
        module
        for module in _imported_modules(tree, ("cora", "engine"))
        if _is_forbidden(module)
    }

    assert bound == {"openai", "torch", "numpy"}


def test_the_walkers_pass_innocent_code(tmp_path: pathlib.Path) -> None:
    innocent = tmp_path / "innocent.py"
    innocent.write_text("import json\n\nfrom cora.domain.chunk import Chunk\n")
    tree = ast.parse(innocent.read_text())

    assert not _imports_streamlit(innocent)
    assert _test_only_imports(innocent) == []
    assert not [
        module
        for module in _imported_modules(tree, ("cora", "engine"))
        if _is_forbidden(module)
    ]


def _bought_by(frontend: str) -> set[str]:
    """The import names a frontend's own manifest pays for: every module the
    distributions it declares contribute, and none a transitive one happens to bring."""
    declared = workspace.requirements(workspace.member_of(f"cora.frontends.{frontend}"))
    return {
        module
        for module, distributions in packages_distributions().items()
        if not set(distributions).isdisjoint(declared)
    }


@pytest.mark.parametrize("frontend", sorted(FRONTEND_TOOLKITS))
def test_a_frontend_is_allowed_only_the_toolkit_its_manifest_buys(
    frontend: str,
) -> None:
    """`FRONTEND_TOOLKITS` is written by hand, so the cheapest way past the rule it
    enforces is to add a name to it. This is what that has to cost: the distribution
    declared in the frontend's own manifest, which ships in the wheel's metadata and is
    installed with it — rather than a word in a test that buys nothing."""
    unbought = FRONTEND_TOOLKITS[frontend] - _bought_by(frontend)

    assert not unbought, (
        f"the {frontend} shell is allowed {sorted(unbought)}, which "
        f"{workspace.location(workspace.member_of(f'cora.frontends.{frontend}'))}"
        "/pyproject.toml does not declare"
    )


def _domain_modules() -> list[ModuleType]:
    """`cora.domain` and everything under it, however deep.

    Walked rather than listed, and the package itself is one of them: a class declared
    in an `__init__` or in a subpackage added later is a class the rule below would
    otherwise never be asked about.
    """
    walked = pkgutil.walk_packages(cora.domain.__path__, prefix="cora.domain.")
    return [cora.domain] + [importlib.import_module(module.name) for module in walked]


def _domain_classes() -> list[type]:
    """Every class those modules declare, under the name it is imported by.

    A name starting with `_` is left out: it is not a value anything outside its own
    module can hold.
    """
    found = [
        kind
        for module in _domain_modules()
        for _, kind in inspect.getmembers(module, inspect.isclass)
        if kind.__module__ == module.__name__ and not kind.__name__.startswith("_")
    ]
    return sorted(found, key=lambda kind: f"{kind.__module__}.{kind.__name__}")


def _is_frozen_dataclass(kind: type) -> bool:
    # `dataclasses` publishes no reader for `frozen`, and the decorator records it here.
    params = getattr(kind, "__dataclass_params__", None)
    return dataclasses.is_dataclass(kind) and bool(params and params.frozen)


def _states_a_shape(kind: type) -> bool:
    """The three things in the domain that are not values: the abstract bases a payload
    or a trace step is declared by, the state a step returns keys of, and the pause that
    is raised.

    Each is asked of the thing itself rather than of a list of names. `isabstract` is
    false for a base that declares no abstract method, so a marker base would be
    reported as a value — the exemptions err towards a failing test, never towards a
    value slipping past.
    """
    return (
        inspect.isabstract(kind)
        or typing.is_typeddict(kind)
        or issubclass(kind, BaseException)
    )


# One from every module that declares a class, so a walk that quietly stops covering a
# module fails here and names it — a count alone would still pass on `errors.py` alone.
REPRESENTATIVE = {
    "cora.domain.agent_state": "AgentState",
    "cora.domain.chat_result": "ChatResult",
    "cora.domain.chunk": "Chunk",
    "cora.domain.citations": "Nothing",
    "cora.domain.conversation": "Turn",
    "cora.domain.decision": "Decision",
    "cora.domain.errors": "CoreError",
    "cora.domain.trace": "TraceStep",
}


def test_every_module_of_the_domain_is_walked() -> None:
    found = {f"{kind.__module__}.{kind.__name__}" for kind in _domain_classes()}

    assert {f"{module}.{name}" for module, name in REPRESENTATIVE.items()} <= found


@pytest.mark.parametrize(
    "kind", _domain_classes(), ids=lambda kind: f"{kind.__module__}.{kind.__name__}"
)
def test_a_value_in_the_domain_is_a_frozen_dataclass(kind: type) -> None:
    """One shape for a value, so it is read by name and cannot be mistaken for what it
    is made of. A `NamedTuple` also unpacks, indexes and compares equal to a plain tuple
    of the same fields — three readings of a value the domain never means, and each one
    a caller can come to depend on.

    Asked of `cora.domain` alone: a value crosses to a caller and is held, while
    `engine.ingestion.Ingested` is a return read apart at each call that makes it, and
    unpacking it there is the point rather than a reading of a value.
    """
    named = f"{kind.__module__}.{kind.__name__}"

    assert _is_frozen_dataclass(kind) or _states_a_shape(kind), (
        f"{named} carries data without being a frozen dataclass"
    )
