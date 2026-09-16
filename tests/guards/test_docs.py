"""Every location the docs claim, checked against the tree.

Only the pages that describe the project as it is now. `docs/sprints/**` is build
history: its paths were true the day they were written and policing them would make
the record of how the code was built follow the code, which is the opposite of what a
record is for.

A location is written relative to the repository, or relative to a package's `cora/`
when it names a module, and carries a trailing slash when it is a directory. A
backticked token holding a slash but no source suffix — a model id like
`openai/gpt-4o-mini` — claims nothing about the tree.
"""

import pathlib
import re

import workspace
from cora.app import config

PRIVACY = "docs/privacy-and-ethics.md"

PAGES = (
    "README.md",
    "CLAUDE.md",
    "docs/index.md",
    "docs/big-picture.md",
    "docs/happy-path.md",
    "docs/the-page.md",
    "docs/data-storage.md",
    "docs/what-it-does.md",
    "docs/what-ships-with-it.md",
    "docs/how-to/get-started.md",
    "docs/how-to/load-plugins.md",
    PRIVACY,
    "docs/workflow.md",
    "docs/how-to/write-a-plugin.md",
    "docs/how-to/watch-a-turn.md",
    "docs/how-to/run-the-react-shell.md",
    "docs/how-to/run-the-telegram-bot.md",
    "docs/tutorial/first-session.md",
)

CONFIGS = ("Makefile",)
SUFFIXES = (".py", ".md", ".toml", "/")

NAMED = re.compile(r"`(CORA_[A-Z0-9_]+)")
TARGET = re.compile(r"`make ([a-z][a-z-]*)`")
LOCATION = r"(?:\.{1,2}/)*\.?[A-Za-z_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.-]*)+"
BACKTICKED = re.compile(rf"`({LOCATION})`")
BARE = re.compile(rf"(?<![`\w/.])({LOCATION})")
CONFIG_PATTERNS = (BACKTICKED, BARE)
NAMESPACES = tuple(sorted(member / "src" / "cora" for member in workspace.members()))


def _references(text: str, patterns: tuple[re.Pattern[str], ...]) -> set[str]:
    return {
        reference
        for pattern in patterns
        for reference in pattern.findall(text)
        if reference.endswith(SUFFIXES)
    }


def _claims() -> list[tuple[str, str]]:
    pages = [(page, (BACKTICKED,)) for page in PAGES]
    configs = [(config, CONFIG_PATTERNS) for config in CONFIGS]
    return sorted(
        {
            (name, reference)
            for name, patterns in pages + configs
            for reference in _references(pathlib.Path(name).read_text(), patterns)
        }
    )


def _resolves(reference: str) -> bool:
    candidates = [pathlib.Path(reference), *(root / reference for root in NAMESPACES)]
    if reference.endswith("/"):
        return any(candidate.is_dir() for candidate in candidates)
    return any(candidate.exists() for candidate in candidates)


def stores() -> dict[str, str]:
    """Every location a deployment can configure, and the variable that moves it.

    Discovered rather than listed: a store added to `cora.app.config` has to reach the
    privacy page, and a list here would be one more place to forget. The variable is
    derived from the constant, which is the naming convention every one of them follows
    — a path setting that broke the convention would fail here, which is the right
    place to notice it. That a setting is really read under the name derived here is
    `tests/cora/app/test_config.py`'s to hold, and it does.
    """
    return {
        name.replace("DEFAULT_", "CORA_"): value
        for name, value in vars(config).items()
        if name.startswith("DEFAULT_") and name.endswith("_PATH")
    }


def test_the_stores_cora_writes_are_one_database_and_one_directory() -> None:
    """What the retired variables would still move, stated so it stays retired: the
    facts, the turns and the passages are one file, and only the documents are kept
    beside it as something a person can read."""
    found = stores()

    assert "CORA_MEMORY_PATH" not in found
    assert "CORA_CONVERSATIONS_PATH" not in found


def test_the_privacy_page_names_every_store_and_the_setting_that_moves_it() -> None:
    """The privacy page's list of what is kept, held against the settings themselves.

    The locations guard below cannot hold it: every store is made at runtime, so a page
    naming one as a directory would claim a path a clean checkout does not have. Read
    off the settings instead, so a store that moves, a store that is added, or a
    variable that is renamed is red until the page says so.
    """
    page = pathlib.Path(PRIVACY).read_text()

    missing = [
        f"{variable} ({kept})"
        for variable, kept in sorted(stores().items())
        if kept not in page or variable not in page
    ]

    assert missing == [], "\n".join(
        ["the privacy page does not account for:", *missing]
    )


def _named_in(page: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(pathlib.Path(page).read_text()))


def _settings() -> set[str]:
    # The frontends are swept rather than imported by name, so the next one's settings
    # are covered by it shipping rather than by somebody adding it here.
    read = set()
    sources = [pathlib.Path(config.__file__ or "").read_text()]
    sources += [
        path.read_text()
        for member in sorted(pathlib.Path("frontends").glob("*/src"))
        for path in sorted(member.rglob("*.py"))
    ]
    for source in sources:
        read |= set(NAMED.findall(source))
        read |= set(re.findall(r'"(CORA_[A-Z0-9_]+)"', source))
    return read | set(stores())


def _plugin_settings_read() -> dict[str, str]:
    found = {}
    for package in sorted(pathlib.Path("plugins").glob("*/src/cora/plugins/*")):
        if package.is_dir():
            found[package.name] = "\n".join(
                path.read_text() for path in package.rglob("*.py")
            )
    return found


def _unread_plugin_setting(name: str) -> str | None:
    rest = name.removeprefix(config.PLUGIN_PREFIX).lower()
    read = _plugin_settings_read()
    for plugin, source in read.items():
        if rest.startswith(f"{plugin}_"):
            setting = rest.removeprefix(f"{plugin}_")
            if setting not in source:
                return f"{plugin} does not read '{setting}'"
            return None
    # A name for no shipped plugin is a plugin the page is teaching you to write.
    return None


def test_every_setting_the_docs_name_is_one_cora_reads() -> None:
    """A page naming a variable nothing reads documents a knob that does nothing —
    which is how `CORA_PLUGIN_FITNESS_UNITS` stood in the docs for a sprint. A plugin's
    settings are checked against the plugin, because the variable names it."""
    read = _settings()
    invented = []
    for page in PAGES:
        for name in sorted(_named_in(page, NAMED)):
            if name.startswith(config.PLUGIN_PREFIX):
                wrong = _unread_plugin_setting(name)
                if wrong is not None:
                    invented.append(f"{page}: {name} — {wrong}")
            elif name not in read:
                invented.append(f"{page}: {name} — nothing reads it")

    assert invented == [], "\n".join(
        ["docs name settings cora does not read:", *invented]
    )


def _recipes() -> dict[str, str]:
    # Variables are spelled out: a target running `$(REACT)` runs what it was set to.
    text = pathlib.Path("Makefile").read_text()
    for name, value in re.findall(r"(?m)^([A-Z_]+)\s*:?=\s*(.+)$", text):
        text = text.replace(f"$({name})", value.strip())
    found: dict[str, str] = {}
    target = None
    for line in text.splitlines():
        if named := re.match(r"^([a-z][a-z-]*):", line):
            target = named.group(1)
            found.setdefault(target, "")
        elif line.startswith("\t") and target:
            found[target] += line
        elif not line.strip():
            target = None
    return found


def test_every_frontend_ships_a_documented_command_that_starts_it() -> None:
    """A frontend nobody can start is a frontend nobody runs, which is the thing the
    one-frontend rule was really about. Read off the workspace rather than listed, so
    the next one is covered by being added."""
    recipes = _recipes()
    documented = {target for page in PAGES for target in _named_in(page, TARGET)}
    unstarted = []
    for _, module in workspace.frontends():
        starts = {name for name, recipe in recipes.items() if module in recipe}
        if not starts:
            unstarted.append(f"{module}: no make target starts it")
        elif not starts & documented:
            unstarted.append(f"{module}: no page names {' or '.join(sorted(starts))}")

    assert unstarted == [], "\n".join(
        [
            "frontends the workspace ships and nobody documents a command for:",
            *unstarted,
        ]
    )


def test_every_make_target_the_docs_name_exists() -> None:
    defined = set(
        re.findall(r"(?m)^([a-z][a-z-]*):", pathlib.Path("Makefile").read_text())
    )
    missing = [
        f"{page}: make {target}"
        for page in PAGES
        for target in _named_in(page, TARGET)
        if target not in defined
    ]

    assert missing == [], "\n".join(
        ["docs name make targets that do not exist:", *missing]
    )


SHARED = ("install", "plugins", "run")
TUTORIAL = "docs/tutorial/first-session.md"
STARTED = "docs/how-to/get-started.md"


def _marked(text: str, name: str) -> str:
    return text.split(f"[start:{name}] -->", 1)[1].split("<!-- --8<--", 1)[0].strip()


def test_the_tutorial_runs_the_same_commands_the_how_to_gives() -> None:
    """Written twice on purpose: a MkDocs snippet renders as its own directive on
    GitHub, and a tutorial whose first step is a line of markup is a tutorial nobody can
    follow. So the two copies are held equal here instead."""
    started = pathlib.Path(STARTED).read_text()
    walked = pathlib.Path(TUTORIAL).read_text()

    drifted = [name for name in SHARED if _marked(started, name) not in walked]

    assert drifted == [], "\n".join(
        [f"the tutorial no longer carries {STARTED}'s block:", *drifted]
    )


def test_every_location_the_docs_claim_exists() -> None:
    stale = [
        f"{name}: {reference}"
        for name, reference in _claims()
        if not _resolves(reference)
    ]
    assert stale == [], "\n".join(["docs point at paths that do not exist:", *stale])
