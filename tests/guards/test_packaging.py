"""What each member declares, read off the manifests.

`test_architecture.py` polices the layer boundary by walking imports; this reads what
the workspace is made of and what a wheel would actually carry. The two are not
redundant: an import the AST walker catches is a rule about source, and a module no
manifest names is shipped as nothing however clean its imports are.

Since the layers collapsed into one distribution the walker is the only thing keeping a
framework out of the engine — the manifest no longer separates them, and the tests that
read that separation went with it.
"""

import pathlib

import pytest

import workspace

MEMBERS = workspace.members()
IDS = [workspace.location(member) for member in MEMBERS]


def _module_roots(member: pathlib.Path) -> list[pathlib.Path]:
    src = member / "src"
    return [
        src / pathlib.Path(*module.split(".")) for module in workspace.modules(member)
    ]


@pytest.mark.parametrize("member", MEMBERS, ids=IDS)
def test_every_member_ships_its_typing_marker(member: pathlib.Path) -> None:
    """`py.typed` is packaged only from inside the module `module-name` names. One
    directory up it reaches neither the wheel nor the sdist, so the layer installs
    untyped while the file sits in the tree looking like it is doing its job — nothing
    else fails on that, which is why the stray copy is asserted against as well."""
    roots = _module_roots(member)
    unmarked = [str(root) for root in roots if not (root / "py.typed").is_file()]
    assert unmarked == [], f"no py.typed inside the packaged module: {unmarked}"

    strays = sorted(
        str(marker)
        for marker in (member / "src").rglob("py.typed")
        if marker.parent not in roots
    )
    assert strays == [], f"py.typed outside the packaged module: {strays}"


@pytest.mark.parametrize("member", MEMBERS, ids=IDS)
def test_no_module_sits_outside_what_its_manifest_names(member: pathlib.Path) -> None:
    """`module-name` as a *list* ships only what it lists, which is what the app's
    manifest now is. So a sixth layer added beside the five, or a loose module dropped
    under `src/cora/`, imports and type-checks and passes the suite while the built
    wheel omits it entirely — the editable install the workspace runs on never reads
    `module-name`."""
    roots = _module_roots(member)
    unshipped = [
        str(path.relative_to(member))
        for path in sorted((member / "src").rglob("*.py"))
        if not any(path.is_relative_to(root) for root in roots)
    ]
    assert unshipped == [], f"outside every declared module: {unshipped}"


def test_the_app_carries_no_plugin_and_names_none() -> None:
    """A plugin is an extension, stated in the one place that can make it false: the
    app neither ships a bundle nor installs one, and its default set is empty. A wheel
    naming a plugin it does not bring cannot start — `load_plugins` raises
    `PluginLoadError` on the module before the first question — so the two halves have
    to agree."""
    from cora.app.config import DEFAULT_PLUGINS

    assert DEFAULT_PLUGINS == ()
    assert not [
        name
        for name in workspace.requirements(workspace.ROOT)
        if name.startswith("cora-")
    ]
    assert not [
        module
        for module in workspace.modules(workspace.ROOT)
        if module.startswith("cora.plugins.")
    ]


# What each plugin reaches outside cora with, as distributions rather than as import
# names — which is why this is stated here and not read off the architecture guard's
# allowance: that one names modules, and the two vocabularies differ the moment a
# distribution's name is not its module's. The frontends' rule below is keyed the same
# way for the same reason.
PLUGIN_REACHES: dict[str, set[str]] = {
    "cora.plugins.fitness": set(),
    "cora.plugins.interview": set(),
    "cora.plugins.security": set(),
    "cora.plugins.travel": {"httpx"},
}


def test_every_plugin_says_what_it_reaches_outside_with() -> None:
    """One added without an entry is asked for nothing, rather than inheriting the
    allowance of the plugin it happens to ship beside."""
    assert {module for _, module in workspace.plugins()} == PLUGIN_REACHES.keys()
