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
    """Raised on rather than `check=True`, which reports the exit status and throws away
    the only part anyone needs — what uv said on stderr."""
    result = subprocess.run(("uv", *args), cwd=REPO, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f"uv {' '.join(args)} failed:\n{result.stderr}")
    return result


def _resolved(dist: str) -> set[str]:
    """Every distribution `dist` would bring with it, read off the lockfile.

    `--frozen --offline` because this runs in the fast tier, which `README.md` promises
    touches no network. `uv tree` locks before it prints, so without them a manifest
    edited since the last lock makes `uv run pytest -q` rewrite `uv.lock` on its way
    past — the one file that is never edited by hand — and go to the index to do it.
    Reading the lock is the whole point: the resolution is the subject, and the lock is
    where it already is.
    """
    tree = _uv("tree", "--package", dist, "--no-dev", "--frozen", "--offline").stdout
    resolved = set(re.findall(r"([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])? v\d", tree))
    assert dist in resolved, (
        f"uv resolved no {dist} — a name nothing ships prints an empty tree and "
        "exits 0, so every claim made about it would hold of nothing"
    )
    return resolved


def test_a_name_the_workspace_does_not_ship_is_an_error() -> None:
    """`uv tree` prints nothing and exits 0 for a package it has never heard of, so a
    renamed distribution would leave the two tests below asserting that `streamlit` is
    absent from an empty set — passing by resolving nothing. The subject has to be found
    before anything can be said about it."""
    with pytest.raises(AssertionError, match="cora-plugin-nonesuch"):
        _resolved("cora-plugin-nonesuch")


SERVES_A_PAGE = frozenset({"starlette", "streamlit"})
"""The frameworks a frontend is written against. `uvicorn` is deliberately not among
them: a server resolves it whatever cora does, so its presence says nothing about the
app owning an interface, and a rule naming it would be false the day it was written."""

RETIRED = "chromadb"
"""The store the index used to be, held out by name: it brought twenty megabytes and a
server's worth of transitive dependencies behind one adapter."""


def test_nothing_in_the_workspace_resolves_the_store_the_index_left() -> None:
    """The index is cora's own SQLite file now, and this is what keeps the store it
    replaced from arriving again under some other member's manifest."""
    reaching = sorted(
        distribution
        for member in workspace.members()
        if RETIRED in _resolved(distribution := workspace.distribution(member))
    )

    assert reaching == [], f"these still bring {RETIRED} in: {reaching}"


def test_the_app_resolves_without_any_user_interface() -> None:
    """What makes a second frontend possible, stated so it can fail — transitively,
    where the manifest sees one edge: a command-line or HTTP shell installs `cora` and
    gets the wiring without the framework a page is written against."""
    assert not _resolved("cora") & SERVES_A_PAGE


def test_nothing_in_the_workspace_resolves_a_second_frontend() -> None:
    """The bar over the whole tree rather than over `cora` alone: the app resolving no
    web toolkit says nothing about a member that ships one, and a frontend nobody runs
    still lands in the lockfile every developer syncs."""
    reaching = sorted(
        distribution
        for member in workspace.members()
        if "streamlit" in _resolved(distribution := workspace.distribution(member))
    )

    assert reaching == [], f"these still bring Streamlit in: {reaching}"


def test_a_plugin_resolves_the_app_and_stops() -> None:
    """Asked of fitness, which is the plugin that takes nothing of its own: equality,
    not a superset, and it pulls the whole app either way — that last part is what the
    layer split used to buy and no longer does. Travel is not asked, because it reaches
    a live service and declares an HTTP client for it; that a plugin may declare only
    what its own allowance names is the packaging guard's rule, not this one's."""
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
