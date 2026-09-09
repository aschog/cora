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
    "docs/data-storage.md",
    PRIVACY,
    "docs/workflow.md",
    "docs/how-to/write-a-plugin.md",
    "docs/how-to/watch-a-turn.md",
    "docs/how-to/run-the-react-shell.md",
    "docs/tutorial/first-session.md",
)

CONFIGS = ("Makefile",)
SUFFIXES = (".py", ".md", ".toml", "/")

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


def test_every_location_the_docs_claim_exists() -> None:
    stale = [
        f"{name}: {reference}"
        for name, reference in _claims()
        if not _resolves(reference)
    ]
    assert stale == [], "\n".join(["docs point at paths that do not exist:", *stale])
