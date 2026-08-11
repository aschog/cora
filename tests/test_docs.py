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

PAGES = ("README.md", "CLAUDE.md", "docs/big-picture.md", "docs/workflow.md")
CONFIGS = (".streamlit/config.toml",)
SUFFIXES = (".py", ".md", ".toml", "/")

BACKTICKED = re.compile(r"`([A-Za-z_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.-]*)+)`")
BARE = re.compile(r"(?<![`\w])([A-Za-z_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.-]*)+)")
NAMESPACES = tuple(sorted(pathlib.Path("packages").glob("*/src/cora")))


def _claims() -> list[tuple[str, str]]:
    pages = [(page, BACKTICKED) for page in PAGES]
    configs = [(config, BARE) for config in CONFIGS]
    return sorted(
        {
            (name, reference)
            for name, pattern in pages + configs
            for reference in pattern.findall(pathlib.Path(name).read_text())
            if reference.endswith(SUFFIXES)
        }
    )


def _resolves(reference: str) -> bool:
    candidates = [pathlib.Path(reference), *(root / reference for root in NAMESPACES)]
    if reference.endswith("/"):
        return any(candidate.is_dir() for candidate in candidates)
    return any(candidate.exists() for candidate in candidates)


def test_every_package_contributes_a_namespace_root() -> None:
    """Counted against the workspace rather than pinned to a number: a location claim is
    resolved against every package, so a package the glob missed would make a stale path
    look fine."""
    members = {
        path.name for path in pathlib.Path("packages").iterdir() if path.is_dir()
    }
    assert {root.parent.parent.name for root in NAMESPACES} == members


def test_a_reference_is_resolved_against_the_packages() -> None:
    """`domain/chunk.py` is a location even though no such path exists from the root:
    the docs name modules the way an import does, from `cora/` down."""
    assert _resolves("domain/chunk.py")
    assert _resolves("frontends/streamlit/")
    assert not _resolves("domain/no_such_module.py")


def test_the_docs_claim_something() -> None:
    assert len(_claims()) > 20, "the extractor found almost nothing — check the regex"


def test_every_location_the_docs_claim_exists() -> None:
    stale = [
        f"{name}: {reference}"
        for name, reference in _claims()
        if not _resolves(reference)
    ]
    assert stale == [], "\n".join(["docs point at paths that do not exist:", *stale])
