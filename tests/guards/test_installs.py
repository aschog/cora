import pathlib
import re
import subprocess
import zipfile

import pytest

import workspace

REPO = workspace.ROOT


def _uv(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(("uv", *args), cwd=REPO, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f"uv {' '.join(args)} failed:\n{result.stderr}")
    return result


def _resolved(dist: str) -> set[str]:
    tree = _uv("tree", "--package", dist, "--no-dev", "--frozen", "--offline").stdout
    resolved = set(re.findall(r"([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])? v\d", tree))
    assert dist in resolved, (
        f"uv resolved no {dist} — a name nothing ships prints an empty tree and "
        "exits 0, so every claim made about it would hold of nothing"
    )
    return resolved


"""The frameworks a frontend is written against. `uvicorn` is deliberately not among
them: a server resolves it whatever cora does, so its presence says nothing about the
app owning an interface, and a rule naming it would be false the day it was written."""

"""The store the index used to be, held out by name: it brought twenty megabytes and a
server's worth of transitive dependencies behind one adapter."""


def test_a_plugin_resolves_the_app_and_stops() -> None:
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


@pytest.mark.integration
def test_every_wheel_carries_the_files_its_package_ships_that_are_not_python(
    wheelhouse: pathlib.Path,
) -> None:
    aside = (".ruff.toml", ".ruff_cache", "__pycache__", ".DS_Store")
    missing = []
    for member in workspace.members():
        src = member / "src"
        with zipfile.ZipFile(_wheel(wheelhouse, member)) as archive:
            shipped = set(archive.namelist())
        missing += [
            f"{workspace.location(member)}: {path.relative_to(src)}"
            for path in sorted(src.rglob("*"))
            if path.is_file()
            and path.suffix != ".py"
            and not any(part in aside for part in path.relative_to(src).parts)
            and str(path.relative_to(src)) not in shipped
        ]
    assert missing == [], f"built but not shipped: {missing}"
