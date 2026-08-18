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


def _on_the_path() -> list[pathlib.Path]:
    """Every directory `pythonpath` puts on `sys.path`, read off the manifest rather
    than named here, so moving the entry moves what this is asserted of."""
    options = workspace.manifest(workspace.ROOT)["tool"]["pytest"]["ini_options"]
    return [workspace.ROOT / entry for entry in options["pythonpath"]]


def test_nothing_on_the_path_is_named_for_a_shipped_namespace() -> None:
    """The rule that matters, and the narrow form of it: `cora` is a namespace no
    distribution owns, so a directory called `cora` inside a `sys.path` entry joins it
    as its first portion and `import cora.domain` can resolve into the test tree rather
    than the install. The mirror under `tests/cora/` is safe for precisely the reason
    this is not — nothing puts `tests/` itself on the path."""
    shipped = {
        module.split(".")[0]
        for member in MEMBERS
        for module in workspace.modules(member)
    }
    colliding = sorted(
        str(path.relative_to(workspace.ROOT))
        for directory in _on_the_path()
        for path in directory.iterdir()
        if path.stem in shipped
    )

    assert colliding == [], f"on sys.path and named for the namespace: {colliding}"


def test_the_globs_reach_every_member_beside_the_app() -> None:
    """The members uv itself would resolve, by running the root manifest's globs. uv
    refuses to sync when a glob matches a directory holding no manifest, so that half is
    covered; the half nothing covers is a manifest at a depth no glob reaches, which uv
    silently ignores — it is simply never locked, never installed, and never built."""
    globs = workspace.manifest(workspace.ROOT)["tool"]["uv"]["workspace"]["members"]
    globbed = {path for pattern in globs for path in workspace.ROOT.glob(pattern)}

    assert globbed == {*MEMBERS} - {workspace.ROOT}


def test_the_workspace_holds_the_app_and_its_extension_points() -> None:
    """Directories are named for what they hold, distributions for the audience that
    installs them."""
    assert {workspace.location(m): workspace.distribution(m) for m in MEMBERS} == {
        ".": "cora",
        "frontends/streamlit": "cora-frontend-streamlit",
        "plugins/fitness": "cora-plugin-fitness",
        "plugins/security": "cora-plugin-security",
    }


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


def test_the_app_owns_no_user_interface() -> None:
    """What makes a second frontend possible, stated so it can fail: a command-line or
    HTTP shell installs `cora` and gets the wiring without a web toolkit."""
    assert "streamlit" not in workspace.requirements(workspace.ROOT)


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


@pytest.mark.parametrize(
    "plugin", [module for _, module in workspace.plugins()], ids=lambda m: m
)
def test_a_plugin_needs_the_app_and_nothing_else(plugin: str) -> None:
    """A plugin is data over the contract: the fitness bundle uses four names —
    `Plugin`, `Tool`, `ToolRefusal`, `InputRejectedError` — and the screen one, and
    neither takes a technology of its own. What a plugin author no longer gets is a
    light install; that was the price of collapsing the layers."""
    member = next(m for m in MEMBERS if plugin in workspace.modules(m))

    assert workspace.requirements(member) == {"cora"}


def test_a_frontend_needs_the_app_and_its_own_toolkit() -> None:
    """One of several possible shells: it takes `cora` for the wiring and the types that
    cross its screen, and the technologies it draws with — the toolkit, and the markdown
    renderer that turns an answer into the HTML a citation can be clicked in. The
    adapters it never names: what it shows is decided by the use cases, what technology
    answers is decided at assembly."""
    requires = workspace.requirements(workspace.ROOT / "frontends" / "streamlit")

    assert requires == {"cora", "streamlit", "markdown-it-py"}
