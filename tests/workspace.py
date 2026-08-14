"""The workspace, read off the manifests. Four suites were parsing `pyproject.toml` for
the same two facts; the next distribution should have one place to be found from."""

import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTENSION_POINTS = ("plugins", "frontends")


def members() -> list[pathlib.Path]:
    """The app is the root; a plugin and a frontend are members beside it, found rather
    than listed so the next one of either is covered too."""
    return [
        ROOT,
        *sorted(
            found.parent
            for point in EXTENSION_POINTS
            for found in (ROOT / point).glob("*/pyproject.toml")
        ),
    ]


def location(member: pathlib.Path) -> str:
    """A member as the docs and the failure messages name it: `.` for the app."""
    return str(member.relative_to(ROOT)) or "."


def manifest(member: pathlib.Path) -> dict:
    return tomllib.loads((member / "pyproject.toml").read_text())


def distribution(member: pathlib.Path) -> str:
    return manifest(member)["project"]["name"]


def modules(member: pathlib.Path) -> list[str]:
    """A manifest may name one module or several: the app carries five layers and the
    guard its default set loads, as six portions of the namespace."""
    declared = manifest(member)["tool"]["uv"]["build-backend"]["module-name"]
    return [declared] if isinstance(declared, str) else list(declared)


def carrier_of(module: str) -> str:
    """The distribution a module ships from."""
    for member in members():
        if module in modules(member):
            return distribution(member)
    raise AssertionError(f"no workspace member ships {module}")


def plugins() -> list[tuple[str, str]]:
    """Every plugin in the workspace as (distribution, module), read off `cora.plugins`
    rather than off the tree: the guard ships from the app and the reference domain from
    a wheel of its own, and a guard written over them covers the next one either way."""
    return sorted(
        (distribution(member), module)
        for member in members()
        for module in modules(member)
        if module.startswith("cora.plugins.")
    )
