import pathlib
import subprocess
from collections.abc import Iterator

import pytest

import workspace

REPO = workspace.ROOT
CONFIG = REPO / "plugins" / "fitness" / "watch" / "config.js"

INSTALLS = "npm i -g @zeppos/zeus-cli"


# The PATH is narrowed to a directory this builds, so whether the Zepp tooling is there
# is what a test said and never what the developer's machine happens to have installed.
def _make(
    tmp_path: pathlib.Path, *overrides: str, zeus: bool = True
) -> subprocess.CompletedProcess[str]:
    fake = tmp_path / "bin"
    fake.mkdir(exist_ok=True)
    # `npm` too: the target installs the extension's one dependency before building, and
    # what is under test is the address it writes, not a package manager.
    for named in ("npm", *(("zeus",) if zeus else ())):
        stand_in = fake / named
        stand_in.write_text(f'#!/bin/sh\necho "{named} $*"\n')
        stand_in.chmod(0o755)
    return subprocess.run(
        ("make", "watch", *overrides),
        cwd=REPO,
        capture_output=True,
        text=True,
        env={"PATH": f"{fake}:/usr/bin:/bin", "HOME": str(tmp_path)},
    )


@pytest.fixture
def config() -> Iterator[pathlib.Path]:
    held = CONFIG.read_text() if CONFIG.is_file() else None
    yield CONFIG
    if held is None:
        CONFIG.unlink(missing_ok=True)
    else:
        CONFIG.write_text(held)


@pytest.mark.integration
def test_the_build_writes_the_address_the_watch_writes_to(
    tmp_path: pathlib.Path, config: pathlib.Path
) -> None:
    built = _make(tmp_path)

    assert built.returncode == 0, built.stderr
    written = config.read_text()
    assert written.startswith("export const NOTICE = 'http://")
    assert written.rstrip().endswith("/api/scopes/fitness/notice'")
    # This machine on the network, never loopback: the phone does the HTTP, and a watch
    # pointed at 127.0.0.1 writes to the phone.
    assert "127.0.0.1" not in written and "localhost" not in written


@pytest.mark.integration
def test_the_address_and_the_field_are_overridable(
    tmp_path: pathlib.Path, config: pathlib.Path
) -> None:
    built = _make(tmp_path, "CORA_AT=http://elsewhere:9000", "WATCH_FIELD=training")

    assert built.returncode == 0, built.stderr
    assert (
        config.read_text().strip()
        == "export const NOTICE = 'http://elsewhere:9000/api/scopes/training/notice'"
    )


@pytest.mark.integration
def test_a_build_without_the_zepp_tooling_stops_and_names_what_installs_it(
    tmp_path: pathlib.Path, config: pathlib.Path
) -> None:
    built = _make(tmp_path, zeus=False)

    assert built.returncode != 0
    assert INSTALLS in built.stdout
