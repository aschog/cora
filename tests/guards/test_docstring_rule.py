"""Where a missing docstring is a finding, and by whose format.

The rule is `ruff`'s to enforce, so it is `ruff` that is asked here — over a snippet on
stdin, named as a file in the package under test. `--stdin-filename` is what makes
`per-file-ignores` apply, so the boundary these read is the one the manifest draws and
not a second copy of it.
"""

import subprocess
import sys
import tomllib
from collections.abc import Callable

import pytest

import workspace

RENDERED = "src/cora/ports/probe.py"
IGNORED = "src/cora/adapters/probe.py"
A_TEST = "tests/cora/test_probe.py"

UNDOCUMENTED = '''"""Module."""


class Thing:
    pass
'''
ARGS_FOR_ONE_OF_THREE = '''"""Module."""


def chunk(text: str, size: int, overlap: int) -> list[str]:
    """Cut text into overlapping windows.

    Args:
        size: Characters, not tokens.
    """
    return [text]
'''
STRAIGHT_INTO_ITS_DESCRIPTION = '''"""Module."""


def chunk(text: str) -> list[str]:
    """Cut text into windows. The windows overlap, so a sentence
    cut in half is still whole in one of them.
    """
    return [text]
'''
DESCRIBES_RATHER_THAN_COMMANDS = '''"""Module."""


def contains(upload: str) -> bool:
    """Whether this upload has already been indexed?"""
    return True
'''

Reported = Callable[[str, str], list[str]]


@pytest.fixture
def reported() -> Reported:
    def codes(source: str, path: str) -> list[str]:
        found = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--output-format",
                "concise",
                "--stdin-filename",
                path,
                "-",
            ],
            input=source,
            cwd=workspace.ROOT,
            capture_output=True,
            text=True,
        )
        return [
            line.split(": ")[1].split()[0]
            for line in found.stdout.splitlines()
            if line.startswith(path)
        ]

    return codes


def test_a_public_class_with_no_docstring_is_reported(reported: Reported) -> None:
    assert reported(UNDOCUMENTED, RENDERED) == ["D101"]


def test_the_same_class_is_not_reported_where_a_backlog_line_still_covers_it(
    reported: Reported,
) -> None:
    """`cora.adapters` is not in the reference, and the packages that are but have not
    been taken yet are ignored the same way — so the list of ignores is also the list of
    what is left."""
    assert reported(UNDOCUMENTED, IGNORED) == []


def test_a_test_function_with_no_docstring_is_reported_by_nothing(
    reported: Reported,
) -> None:
    """A test's name carries its behaviour and no page renders it."""
    assert (
        reported("def test_a_thing_happens() -> None:\n    assert True\n", A_TEST) == []
    )


def test_an_args_section_may_name_one_parameter_of_three(reported: Reported) -> None:
    """`D417` would demand all three, which is what turns a section into a restatement
    of the annotations beside it. Documented here is the one whose meaning the type
    cannot carry."""
    assert reported(ARGS_FOR_ONE_OF_THREE, RENDERED) == []


def test_a_summary_running_straight_into_its_description_is_reported(
    reported: Reported,
) -> None:
    """A page opens on the summary, so it is a line and not the first half of a
    paragraph."""
    assert reported(STRAIGHT_INTO_ITS_DESCRIPTION, RENDERED) == ["D205"]


def test_the_format_is_decided_in_one_place(reported: Reported) -> None:
    """A summary that describes rather than commands, and ends in a question mark, is
    Google's to allow — every other convention ruff knows reports both. Nothing in the
    snippet says which convention it is written in: the manifest is the only thing that
    decides."""
    manifest = tomllib.loads((workspace.ROOT / "pyproject.toml").read_text())

    assert manifest["tool"]["ruff"]["lint"]["pydocstyle"]["convention"] == "google"
    assert reported(DESCRIBES_RATHER_THAN_COMMANDS, RENDERED) == []
