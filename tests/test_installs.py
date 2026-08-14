"""The manifests as an install, not a declaration.

`test_packaging.py` reads what a manifest names and `test_architecture.py` walks what
the source imports; both run inside the development environment, where every framework
is importable, nothing is ever missing and no wheel is ever built.

The cheap half asks the resolver, which is transitive where a manifest sees one edge.
The expensive half builds the wheels and reads what is inside them, and is marked
integration for it: `module-name` is the one thing no other gate can be wrong about,
because the editable install the workspace runs on never reads it.
"""

import pathlib
import re
import subprocess
import zipfile

import pytest

import workspace

REPO = workspace.ROOT


def _uv(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("uv", *args), cwd=REPO, capture_output=True, text=True, check=True
    )


def _resolved(dist: str) -> set[str]:
    """Every distribution `dist` would bring with it, read off the lockfile."""
    tree = _uv("tree", "--package", dist, "--no-dev").stdout
    return set(re.findall(r"([A-Za-z0-9][A-Za-z0-9._-]*) v\d", tree))


def test_the_app_resolves_without_any_user_interface() -> None:
    """What makes a second frontend possible, stated so it can fail — transitively,
    where the manifest sees one edge: a command-line or HTTP shell installs `cora` and
    gets the wiring without a web toolkit."""
    assert "streamlit" not in _resolved("cora")


def test_a_plugin_resolves_the_app_and_stops() -> None:
    """A plugin takes nothing of its own — no toolkit, no second technology. Equality,
    not a superset: a plugin that grew a direct dependency of its own is exactly what
    this is here to catch, and it pulls the whole app either way. That last part is what
    the layer split used to buy and no longer does."""
    assert _resolved("cora-plugin-fitness") == {
        "cora-plugin-fitness",
        *_resolved("cora"),
    }


@pytest.fixture(scope="session")
def wheelhouse(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    built = tmp_path_factory.mktemp("wheelhouse")
    _uv("build", "--all-packages", "--out-dir", str(built))
    return built


def _wheel(wheelhouse: pathlib.Path, member: pathlib.Path) -> pathlib.Path:
    manifest = workspace.manifest(member)
    stem = manifest["project"]["name"].replace("-", "_")
    version = manifest["project"]["version"]
    found = list(wheelhouse.glob(f"{stem}-{version}-*.whl"))
    assert len(found) == 1, f"{workspace.location(member)}: one wheel expected, {found}"
    return found[0]


@pytest.mark.integration
def test_every_wheel_carries_every_module_its_package_holds(
    wheelhouse: pathlib.Path,
) -> None:
    """A module the manifest forgot to name is not an error anywhere else in the
    toolchain — it just is not in here. Now that the app's `module-name` is a list of
    five, this is the gate a sixth layer would fail."""
    missing = []
    for member in workspace.members():
        src = member / "src"
        with zipfile.ZipFile(_wheel(wheelhouse, member)) as archive:
            shipped = set(archive.namelist())
        missing += [
            f"{workspace.location(member)}: {path.relative_to(src)}"
            for path in sorted(src.rglob("*.py"))
            if str(path.relative_to(src)) not in shipped
        ]
    assert missing == [], f"built but not shipped: {missing}"
