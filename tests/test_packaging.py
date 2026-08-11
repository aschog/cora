"""What each layer is allowed to depend on, read off the manifests.

`test_architecture.py` polices the same boundary by walking imports; this reads the
declaration behind it. The two are not redundant: an import the AST walker would
catch cannot even resolve once the distribution does not ship the dependency, and a
dependency added to the wrong manifest is a mistake no import test would notice until
something used it.
"""

import pathlib
import re

import tomllib

PACKAGES = pathlib.Path("packages")
LAYERS = ("api", "engine", "adapters", "fitness", "app")
HEAVY = frozenset(
    {
        "chromadb",
        "langchain-openai",
        "langgraph",
        "rank-bm25",
        "sentence-transformers",
        "streamlit",
    }
)


def _manifest(name: str) -> dict:
    return tomllib.loads((PACKAGES / name / "pyproject.toml").read_text())


def _requires(name: str) -> set[str]:
    """Distribution names only — the version specifier is not the subject here. Cut at
    the first specifier character, so `~=` yields the name and not `streamlit~`."""
    declared = _manifest(name)["project"]["dependencies"]
    return {re.split(r"[<>=!~\[;\s]", requirement)[0] for requirement in declared}


def _module_roots(name: str) -> list[pathlib.Path]:
    """A manifest may name one module or several: `cora-api` carries `cora.domain` and
    `cora.ports` as two portions of the namespace, so `module-name` is a list there."""
    declared = _manifest(name)["tool"]["uv"]["build-backend"]["module-name"]
    modules = [declared] if isinstance(declared, str) else declared
    src = PACKAGES / name / "src"
    return [src / pathlib.Path(*module.split(".")) for module in modules]


def test_the_workspace_holds_exactly_its_layers() -> None:
    """Directories are named for the layer, distributions for the audience that installs
    them. Nothing in the tree may be called `cora`: the root goes on `sys.path` for
    anything run from it, and a directory of that name joins the namespace as its first
    portion — which is enough to make `import cora.fitness` resolve to an empty
    phantom."""
    assert {path.name for path in PACKAGES.iterdir() if path.is_dir()} == set(LAYERS)
    assert {layer: _manifest(layer)["project"]["name"] for layer in LAYERS} == {
        "api": "cora-api",
        "engine": "cora-engine",
        "adapters": "cora-adapters",
        "fitness": "cora-fitness",
        "app": "cora-app",
    }


def test_every_layer_ships_its_typing_marker() -> None:
    """`py.typed` is packaged only from inside the module `module-name` names. One
    directory up it reaches neither the wheel nor the sdist, so the layer installs
    untyped while the file sits in the tree looking like it is doing its job — nothing
    else fails on that, which is why the stray copy is asserted against as well."""
    unmarked = [
        str(root)
        for layer in LAYERS
        for root in _module_roots(layer)
        if not (root / "py.typed").is_file()
    ]
    assert unmarked == [], f"no py.typed inside the packaged module: {unmarked}"

    strays = sorted(
        str(marker)
        for layer in LAYERS
        for marker in (PACKAGES / layer / "src").rglob("py.typed")
        if marker.parent not in _module_roots(layer)
    )
    assert strays == [], f"py.typed outside the packaged module: {strays}"


def test_core_declares_no_framework() -> None:
    """The purity rule, as metadata: a core that never installs Chroma or LangGraph
    cannot import them by accident, whatever a walker does or does not catch."""
    assert not _requires("engine") & HEAVY


def test_core_reads_no_file_format_of_its_own() -> None:
    """Which formats can be read is the adapters' business: core is handed loaders
    through a port, so pypdf ships with the loader that needs it."""
    assert "pypdf" not in _requires("engine")
    assert "pypdf" in _requires("adapters")


def test_the_contract_declares_nothing_at_all() -> None:
    """What a plugin author installs: no layer, and no third party either. The engine is
    what *checks* a tool's schema, so `jsonschema` is the engine's dependency — the
    contract only says a tool has one."""
    assert _requires("api") == set()


def test_the_engine_needs_the_contract_and_no_other_layer() -> None:
    assert {name for name in _requires("engine") if name.startswith("cora-")} == {
        "cora-api"
    }


def test_a_plugin_needs_the_contract_alone() -> None:
    """A plugin author installs one package, and it is not the engine: the fitness
    bundle uses four names — `Plugin`, `Tool`, `ToolRefusal`, `InputRejectedError`."""
    assert _requires("fitness") == {"cora-api"}


def test_the_adapters_bind_the_contract_to_its_technologies() -> None:
    """An adapter fills a slot, so the contract is all it needs to know. Depending
    on the engine would tie a technology to one version of the use cases it serves."""
    requires = _requires("adapters")

    assert "cora-engine" not in requires
    assert "cora-api" in requires
    assert HEAVY - {"streamlit"} <= requires, "an adapter's technology went missing"
    assert "streamlit" not in requires, "the UI is an entrypoint, not an adapter"


def test_the_app_wires_the_layers_and_owns_the_ui() -> None:
    requires = _requires("app")

    assert {"cora-engine", "cora-adapters", "streamlit"} <= requires
    assert "cora-fitness" not in requires, (
        "the shipped app names its default plugin in config, but must not depend on a "
        "domain: that is what keeps the agent domain-agnostic"
    )
