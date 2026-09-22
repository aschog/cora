import pathlib
import re
import tomllib


def _root() -> pathlib.Path:
    for parent in pathlib.Path(__file__).resolve().parents:
        manifest = parent / "pyproject.toml"
        if manifest.is_file() and "[tool.uv.workspace]" in manifest.read_text():
            return parent
    raise RuntimeError("no workspace root above " + __file__)


ROOT = _root()
EXTENSION_POINTS = ("plugins", "frontends")


def members() -> list[pathlib.Path]:
    return [
        ROOT,
        *sorted(
            found.parent
            for point in EXTENSION_POINTS
            for found in (ROOT / point).glob("*/pyproject.toml")
        ),
    ]


def location(member: pathlib.Path) -> str:
    return str(member.relative_to(ROOT)) or "."


def manifest(member: pathlib.Path) -> dict:
    return tomllib.loads((member / "pyproject.toml").read_text())


def distribution(member: pathlib.Path) -> str:
    return manifest(member)["project"]["name"]


def requirements(member: pathlib.Path) -> set[str]:
    declared = manifest(member)["project"].get("dependencies", ())
    return {re.split(r"[<>=!~\[;\s]", requirement)[0] for requirement in declared}


def modules(member: pathlib.Path) -> list[str]:
    declared = manifest(member)["tool"]["uv"]["build-backend"]["module-name"]
    return [declared] if isinstance(declared, str) else list(declared)


def frontends() -> list[tuple[str, str]]:
    return sorted(
        (distribution(member), module)
        for member in members()
        for module in modules(member)
        if module.startswith("cora.frontends.")
    )


def plugins() -> list[tuple[str, str]]:
    return sorted(
        (distribution(member), module)
        for member in members()
        for module in modules(member)
        if module.startswith("cora.plugins.")
    )
