import pathlib
import re

import workspace
from cora.app import config

FRONT_DOOR = workspace.ROOT / "README.md"

LINKED = re.compile(r"\]\((docs/[^)#\s]+)")
NAMED = re.compile(r"`(CORA_[A-Z0-9_]+)")
TARGET = re.compile(r"`make ([a-z][a-z-]*)`")


def _front_door() -> str:
    return FRONT_DOOR.read_text()


def test_every_docs_link_the_front_door_makes_resolves() -> None:
    broken = [
        linked
        for linked in sorted(set(LINKED.findall(_front_door())))
        if not (workspace.ROOT / linked).exists()
    ]

    assert broken == [], "\n".join(["the front door links what is not there:", *broken])


def test_every_make_target_the_front_door_names_exists() -> None:
    recipes = re.compile(r"(?m)^([a-z][a-z-]*):")
    defined = set(recipes.findall((workspace.ROOT / "Makefile").read_text()))

    missing = [
        f"make {target}"
        for target in sorted(set(TARGET.findall(_front_door())))
        if target not in defined
    ]

    assert missing == [], "\n".join(
        ["the front door names make targets that do not exist:", *missing]
    )


def _settings_cora_reads() -> set[str]:
    # The frontends are swept rather than named, so the next one's settings are covered
    # by it shipping rather than by somebody adding it here.
    sources = [pathlib.Path(config.__file__ or "").read_text()]
    sources += [
        path.read_text()
        for member in sorted((workspace.ROOT / "frontends").glob("*/src"))
        for path in sorted(member.rglob("*.py"))
    ]
    read = {
        name.replace("DEFAULT_", "CORA_")
        for name in vars(config)
        if name.startswith("DEFAULT_") and name.endswith("_PATH")
    }
    for source in sources:
        read |= set(NAMED.findall(source))
        read |= set(re.findall(r'"(CORA_[A-Z0-9_]+)"', source))
    return read


def _plugin_setting_unread(name: str) -> str | None:
    rest = name.removeprefix(config.PLUGIN_PREFIX).lower()
    for package in sorted((workspace.ROOT / "plugins").glob("*/src/cora/plugins/*")):
        if package.is_dir() and rest.startswith(f"{package.name}_"):
            source = "\n".join(path.read_text() for path in package.rglob("*.py"))
            setting = rest.removeprefix(f"{package.name}_")
            return None if setting in source else f"{package.name} does not read it"
    # A name for no shipped plugin is a plugin the page is teaching you to write.
    return None


def test_every_setting_the_front_door_names_is_one_cora_reads() -> None:
    read = _settings_cora_reads()

    invented = []
    for name in sorted(set(NAMED.findall(_front_door()))):
        if name.startswith(config.PLUGIN_PREFIX):
            if (wrong := _plugin_setting_unread(name)) is not None:
                invented.append(f"{name} — {wrong}")
        elif name not in read:
            invented.append(f"{name} — nothing reads it")

    assert invented == [], "\n".join(
        ["the front door names settings cora does not read:", *invented]
    )
