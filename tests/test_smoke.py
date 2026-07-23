"""Smoke test proving the package wiring and test runner work."""

import core


def test_package_exposes_version() -> None:
    assert core.__version__ == "0.1.0"
