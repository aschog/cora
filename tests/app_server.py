import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import IO

APP_MODULE = "cora.app.ui.streamlit_app"
READY_TIMEOUT = 180.0
POLL_INTERVAL = 0.25
INHERITED_KNOBS = ("CORA_", "STREAMLIT_")


def find_free_port() -> int:
    """Binding port 0 and reading back the assignment leaves a race: the port is
    free when we look, not necessarily when Streamlit claims it. Every scheme has
    that race; this is the shortest one."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@dataclass(frozen=True)
class AppServer:
    url: str
    process: subprocess.Popen[bytes]
    log: IO[bytes]

    @property
    def is_running(self) -> bool:
        return self.process.poll() is None

    def health(self) -> str:
        with urllib.request.urlopen(f"{self.url}/_stcore/health", timeout=5) as reply:
            return reply.read().decode()

    def output(self) -> str:
        self.log.seek(0)
        return self.log.read().decode(errors="replace")


@contextmanager
def running_app(
    *, base_url: str, api_key: str | None, db_path: Path, model: str = "stub-model"
) -> Iterator[AppServer]:
    port = find_free_port()
    # A pipe would deadlock once the app fills the buffer, and the app is chatty.
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(
            _command(port),
            stdout=log,
            stderr=subprocess.STDOUT,
            env=app_env(base_url, api_key, db_path, model),
        )
        server = AppServer(url=f"http://127.0.0.1:{port}", process=process, log=log)
        try:
            _await_ready(server)
            yield server
        finally:
            _stop(process)
            # pytest shows captured output only for failing tests, so this is
            # quiet when green and the whole server-side story when red.
            print(server.output())


def app_env(
    base_url: str, api_key: str | None, db_path: Path, model: str
) -> dict[str, str]:
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(INHERITED_KNOBS)
    } | {
        "OPENROUTER_BASE_URL": base_url,
        "CORA_MODEL": model,
        "CORA_DB_PATH": str(db_path),
        # A set HTTP_PROXY turns the loopback call to the stub into a connection
        # error, and the client caches its transport, so this must be set up front.
        "NO_PROXY": "127.0.0.1,localhost",
    }
    if api_key is None:
        env.pop("OPENROUTER_API_KEY", None)
    else:
        env["OPENROUTER_API_KEY"] = api_key
    return env


def _command(port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        _script_path(),
        "--server.headless=true",  # also suppresses the first-run email prompt
        f"--server.port={port}",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
        "--global.developmentMode=false",
    ]


def _script_path() -> str:
    spec = importlib.util.find_spec(APP_MODULE)
    if spec is None or spec.origin is None:
        raise RuntimeError(f"cannot locate {APP_MODULE}")
    return spec.origin


def _await_ready(server: AppServer) -> None:
    deadline = time.monotonic() + READY_TIMEOUT
    while time.monotonic() < deadline:
        if not server.is_running:
            raise RuntimeError(f"the app exited before serving:\n{server.output()}")
        try:
            if server.health() == "ok":
                return
        except (urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(POLL_INTERVAL)
    raise RuntimeError(f"the app never became healthy:\n{server.output()}")


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
