"""Smoke test proving the package wiring and test runner work."""

import cora


def test_package_exposes_version() -> None:
    assert cora.__version__ == "0.1.0"
