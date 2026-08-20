import os
import pathlib
import subprocess
import sys

import pytest

import workspace

QUIET_FORK = {
    "NO_MKDOCS_2_WARNING": "true",
    "DISABLE_MKDOCS_2_WARNING": "true",
}


@pytest.fixture(scope="session")
def built(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    out = tmp_path_factory.mktemp("site")
    build = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(out)],
        cwd=workspace.ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, **QUIET_FORK},
    )
    assert build.returncode == 0, build.stderr
    return out
