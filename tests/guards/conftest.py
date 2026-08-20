import pathlib
import subprocess
import sys

import pytest

import workspace


@pytest.fixture(scope="session")
def built(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    out = tmp_path_factory.mktemp("site")
    build = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(out)],
        cwd=workspace.ROOT,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stderr
    return out
