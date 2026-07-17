"""Smoke test proving the package wiring and test runner work."""

import docchat


def test_package_exposes_version() -> None:
    assert docchat.__version__ == "0.1.0"
