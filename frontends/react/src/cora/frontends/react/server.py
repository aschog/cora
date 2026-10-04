"""The process the deployment runs: cora served over HTTP, live over its plugins
folder — a plugin dropped there is installed by the next request, no restart.

The build it serves is looked for beside the package rather than shipped inside it —
`ui/dist` is Vite's output, not a Python module. Nothing is mounted when it is absent,
which is a dev machine running the page on Vite instead.
"""

import ipaddress
import os
import pathlib
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field

import uvicorn

from cora.app.assembly import live
from cora.app.config import Config, int_setting
from cora.domain.errors import ConfigurationError, CoreError
from cora.frontends.react.api import api

DEFAULT_UI = pathlib.Path(__file__).resolve().parents[4] / "ui" / "dist"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
LOWEST_PORT = 1


def ui_path(env: Mapping[str, str]) -> pathlib.Path:
    """Where the built page is. An installed wheel has no `ui/` beside it, so a
    deployment that serves one names it; a blank is not a name, as everywhere else."""
    return pathlib.Path(env.get("CORA_UI_PATH", "").strip() or DEFAULT_UI)


def port(env: Mapping[str, str]) -> int:
    """Which port to serve on, read through the same contract as every other number the
    app takes from the environment: a mistyped one is a sentence naming the variable,
    not a `ValueError` out of uvicorn's arguments."""
    return int_setting(env, "CORA_PORT", DEFAULT_PORT, minimum=LOWEST_PORT)


@dataclass(frozen=True)
class Serving:
    host: str
    port: int
    token: str | None = field(default=None, repr=False)


def settings(env: Mapping[str, str]) -> Serving:
    host = env.get("CORA_HOST", "").strip() or DEFAULT_HOST
    opt_in = env.get("CORA_NETWORK", "").strip()
    if opt_in not in {"", "0", "1"}:
        raise ConfigurationError("CORA_NETWORK must be 0 or 1 (or unset).")
    network = opt_in == "1"
    if not network and not _loopback(host):
        raise ConfigurationError(
            "Non-loopback binding requires CORA_NETWORK=1 and CORA_API_TOKEN."
        )
    token = env.get("CORA_API_TOKEN", "").strip() if network else None
    if network and not token:
        raise ConfigurationError("CORA_API_TOKEN is required when CORA_NETWORK=1.")
    return Serving(host=host, port=port(env), token=token)


def _loopback(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def serve() -> None:
    """Everything that can be refused is refused before anything is built: a mistyped
    port costs the operator a sentence rather than the wait for a model to load. What
    the app raises was written to be read by whoever ran it, so that is what reaches
    them — the traceback it arrived under buries the one line they can act on."""
    try:
        chosen = settings(os.environ)
        config = Config.from_env()
        served = api(live(config), ui=ui_path(os.environ))
    except CoreError as refused:
        # Written here rather than left to `SystemExit` to carry: an exit whose argument
        # is a string is only printed if nothing catches it on the way out.
        print(f"cora cannot start: {refused.user_message}", file=sys.stderr)
        raise SystemExit(1) from None
    uvicorn.run(
        served,
        host=chosen.host,
        port=chosen.port,
    )


if __name__ == "__main__":
    serve()
