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
from pages import PAGES

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


def test_every_member_contributes_a_namespace_root() -> None:
    """Two discoveries compared, not one restated: the namespace roots are built off the
    manifests, and this walks the tree for them instead. A location claim is resolved
    against every root, so a member either discovery missed would make a stale path look
    fine."""
    found = {
        path
        for pattern in ("src/cora", "*/*/src/cora")
        for path in workspace.ROOT.glob(pattern)
        if path.is_dir()
    }

    assert found == {*NAMESPACES}


def test_a_reference_is_resolved_against_the_packages() -> None:
    """`domain/chunk.py` is a location even though no such path exists from the root:
    the docs name modules the way an import does, from `cora/` down."""
    assert _resolves("domain/chunk.py")
    assert _resolves("frontends/react/")
    assert not _resolves("domain/no_such_module.py")


def test_a_config_is_read_for_the_paths_its_comments_write_like_prose() -> None:
    """A comment in a config names a file the way a page does, in backticks — so reading
    configs bare let a comment go on pointing at a file the tree no longer has. A path
    is claimed from its start: what follows a slash is a segment, not a second claim."""
    claims = _claims()

    assert ("Makefile", "tests/guards/test_docs.py") in claims
    assert ("Makefile", "guards/test_docs.py") not in claims


def test_a_path_is_claimed_from_its_dot_as_readily_as_from_a_letter() -> None:
    """A leading dot is part of the name, not punctuation in front of it: `.githooks/`
    is a directory and `./docs/` is the same directory as `docs/`. Reading past the dot
    would claim a fragment the tree does not have, and skipping the token would leave a
    stale path unchecked — the two ways this guard can be wrong about one character."""
    assert _references("the hooks are in `.githooks/`.", CONFIG_PATTERNS) == {
        ".githooks/"
    }
    assert _references("see ./docs/big-picture.md", CONFIG_PATTERNS) == {
        "./docs/big-picture.md"
    }


def test_the_docs_claim_something() -> None:
    assert len(_claims()) > 20, "the extractor found almost nothing — check the regex"


def test_every_location_the_docs_claim_exists() -> None:
    stale = [
        f"{name}: {reference}"
        for name, reference in _claims()
        if not _resolves(reference)
    ]
    assert stale == [], "\n".join(["docs point at paths that do not exist:", *stale])
