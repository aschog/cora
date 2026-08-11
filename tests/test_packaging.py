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
LAYERS = ("core", "adapters", "fitness", "app")
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


def test_the_workspace_holds_exactly_the_four_layers() -> None:
    """Directories are named for the layer, distributions for the project. Nothing in
    the tree may be called `cora`: the root goes on `sys.path` for anything run from
    it, and a directory of that name joins the namespace as its first portion — which
    is enough to make `import cora.fitness` resolve to an empty phantom."""
    assert {path.name for path in PACKAGES.iterdir() if path.is_dir()} == {
        "core",
        "adapters",
        "fitness",
        "app",
    }
    assert {layer: _manifest(layer)["project"]["name"] for layer in LAYERS} == {
        "core": "cora-core",
        "adapters": "cora-adapters",
        "fitness": "cora-fitness",
        "app": "cora-app",
    }


def test_core_declares_no_framework() -> None:
    """The purity rule, as metadata: a core that never installs Chroma or LangGraph
    cannot import them by accident, whatever a walker does or does not catch."""
    assert not _requires("core") & HEAVY


def test_core_depends_on_no_other_layer() -> None:
    assert not {name for name in _requires("core") if name.startswith("cora-")}


def test_a_plugin_needs_the_core_alone() -> None:
    """A plugin author installs one package. Wanting an adapter here would mean the
    domain had been written against a technology."""
    assert _requires("fitness") == {"cora-core"}


def test_the_adapters_bind_the_core_to_its_technologies() -> None:
    requires = _requires("adapters")

    assert "cora-core" in requires
    assert HEAVY - {"streamlit"} <= requires, "an adapter's technology went missing"
    assert "streamlit" not in requires, "the UI is an entrypoint, not an adapter"


def test_the_app_wires_the_layers_and_owns_the_ui() -> None:
    requires = _requires("app")

    assert {"cora-core", "cora-adapters", "streamlit"} <= requires
    assert "cora-fitness" not in requires, (
        "the shipped app names its default plugin in config, but must not depend on a "
        "domain: that is what keeps the agent domain-agnostic"
    )
