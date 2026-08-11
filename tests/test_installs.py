"""The layer boundary as an install, not a declaration.

`test_packaging.py` reads what a manifest allows and `test_architecture.py` walks what
the source imports; both run inside the development environment, where every framework
is importable and nothing is ever missing. This builds the wheels and installs one
distribution into an empty environment, which is the only place "a plugin needs the
contract alone" can actually fail.

Integration tier: it builds every wheel in the workspace and resolves what they require.
"""

import json
import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent


def _uv(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("uv", *args), cwd=REPO, capture_output=True, text=True, check=True
    )


@pytest.fixture(scope="session")
def wheelhouse(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    built = tmp_path_factory.mktemp("wheelhouse")
    _uv("build", "--all-packages", "--out-dir", str(built))
    return built


def _install(env: pathlib.Path, wheelhouse: pathlib.Path, *dists: str) -> pathlib.Path:
    _uv("venv", str(env))
    python = env / "bin" / "python"
    _uv(
        "pip",
        "install",
        "--python",
        str(python),
        "--find-links",
        str(wheelhouse),
        *dists,
    )
    return python


def _probe(python: pathlib.Path, code: str) -> str:
    done = subprocess.run(
        (str(python), "-c", code), capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def _installed(python: pathlib.Path) -> set[str]:
    """Every distribution present, cora's and its dependencies' alike. `uv venv` seeds
    nothing, so the set is exactly what the install pulled in."""
    listing = _probe(
        python,
        "import json;from importlib.metadata import distributions;"
        "print(json.dumps(sorted(d.metadata['Name'] for d in distributions())))",
    )
    return set(json.loads(listing))


def _imports(python: pathlib.Path, module: str) -> bool:
    """Really imported, not merely found: a plugin that resolves its own imports against
    the contract alone is the claim, and `find_spec` raises rather than answering when
    the namespace above the module is itself absent."""
    return (
        _probe(
            python,
            "import importlib\n"
            "try:\n"
            f"    importlib.import_module({module!r})\n"
            "except ImportError:\n"
            "    print(False)\n"
            "else:\n"
            "    print(True)\n",
        )
        == "True"
    )


@pytest.mark.integration
def test_an_empty_environment_has_nothing_in_it(
    tmp_path: pathlib.Path, wheelhouse: pathlib.Path
) -> None:
    """The measuring stick: without this, an install assertion could pass because the
    probe sees nothing at all."""
    _uv("venv", str(tmp_path / "empty"))
    python = tmp_path / "empty" / "bin" / "python"

    assert _installed(python) == set()
    assert not _imports(python, "cora.plugins.fitness")


def _import_failures(python: pathlib.Path, package: str) -> list[str]:
    """Every module under `package`, imported for real. A leak out of the contract
    shows up as an unresolvable import — the guarantee the AST walker used to give the
    domain, except asked of an environment that genuinely lacks the engine rather than
    of one where everything happens to be present."""
    listing = _probe(
        python,
        "import importlib, json, pkgutil\n"
        f"pkg = importlib.import_module({package!r})\n"
        "broken = []\n"
        "for found in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + '.'):\n"
        "    try:\n"
        "        importlib.import_module(found.name)\n"
        "    except Exception as exc:\n"
        "        broken.append(f'{found.name}: {exc!r}')\n"
        "print(json.dumps(broken))\n",
    )
    return json.loads(listing)


@pytest.mark.integration
def test_a_plugin_installs_the_contract_and_nothing_else(
    tmp_path: pathlib.Path, wheelhouse: pathlib.Path
) -> None:
    """The story, as an environment: four names is what the fitness bundle uses, so the
    engine, the adapters and every framework stay out of a plugin author's venv."""
    python = _install(tmp_path / "plugin", wheelhouse, "cora-fitness")

    assert _imports(python, "cora.plugins.fitness")
    assert _installed(python) == {"cora-fitness", "cora-api"}


@pytest.mark.integration
def test_the_contract_stands_up_with_nothing_installed_beside_it(
    tmp_path: pathlib.Path, wheelhouse: pathlib.Path
) -> None:
    """Stdlib only, and self-contained: every domain and port module imports with no
    engine, no adapter and no third party present. This is what lets the walker's
    domain-may-not-import-the-service-layer guard be deleted rather than moved."""
    python = _install(tmp_path / "contract", wheelhouse, "cora-api")

    assert _installed(python) == {"cora-api"}
    assert _import_failures(python, "cora.domain") == []
    assert _import_failures(python, "cora.ports") == []
