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
    roots = _module_roots(member)
    unshipped = [
        str(path.relative_to(member))
        for path in sorted((member / "src").rglob("*.py"))
        if not any(path.is_relative_to(root) for root in roots)
    ]
    assert unshipped == [], f"outside every declared module: {unshipped}"


def test_the_app_carries_no_plugin_and_names_none() -> None:
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
    "cora.plugins.vocab": set(),
}


def test_every_plugin_says_what_it_reaches_outside_with() -> None:
    assert {module for _, module in workspace.plugins()} == PLUGIN_REACHES.keys()


EXCLUDED = ["**/.ruff.toml", "**/.ruff_cache"]


@pytest.mark.parametrize("member", MEMBERS, ids=IDS)
def test_no_member_ships_the_lint_config_it_is_governed_by(
    member: pathlib.Path,
) -> None:
    build = workspace.manifest(member).get("tool", {}).get("uv", {})
    backend = build.get("build-backend", {})

    assert backend.get("wheel-exclude") == EXCLUDED, (
        f"{workspace.location(member)} would ship its lint config in the wheel"
    )
    assert backend.get("source-exclude") == EXCLUDED, (
        f"{workspace.location(member)} would ship its lint config in the sdist"
    )
