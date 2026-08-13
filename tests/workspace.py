"""The workspace, read off the manifests. Four suites were parsing `pyproject.toml` for
the same two facts; the next distribution should have one place to be found from."""

import pathlib

import tomllib

PACKAGES = pathlib.Path(__file__).resolve().parent.parent / "packages"


def members() -> list[pathlib.Path]:
    """A member is a directory with a manifest, found rather than listed: the tree nests
    where the namespace nests, so `plugins/fitness` is as much a member as `engine`."""
    return sorted(path.parent for path in PACKAGES.rglob("pyproject.toml"))


def manifest(member: pathlib.Path) -> dict:
    return tomllib.loads((member / "pyproject.toml").read_text())


def distribution(member: pathlib.Path) -> str:
    return manifest(member)["project"]["name"]


def modules(member: pathlib.Path) -> list[str]:
    """A manifest may name one module or several: `cora-api` carries `cora.domain` and
    `cora.ports` as two portions of the namespace."""
    declared = manifest(member)["tool"]["uv"]["build-backend"]["module-name"]
    return [declared] if isinstance(declared, str) else list(declared)


def carrier_of(module: str) -> str:
    """The distribution a module ships from."""
    for member in members():
        if module in modules(member):
            return distribution(member)
    raise AssertionError(f"no workspace member ships {module}")


def plugins() -> list[tuple[str, str]]:
    """Every plugin in the workspace as (distribution, module), so a guard written over
    them covers the next one too."""
    return sorted(
        (distribution(member), module)
        for member in members()
        if member.parent.name == "plugins"
        for module in modules(member)
    )
