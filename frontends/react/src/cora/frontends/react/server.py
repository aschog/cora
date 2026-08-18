"""The process the deployment runs: cora assembled once, served over HTTP.

The build it serves is looked for beside the package rather than shipped inside it —
`ui/dist` is Vite's output, not a Python module. Nothing is mounted when it is absent,
which is a dev machine running the page on Vite instead.
"""

import os
import pathlib
from collections.abc import Mapping

import uvicorn

from cora.app.assembly import build
from cora.app.config import Config, _int
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
    not a `ValueError` out of uvicorn's arguments. Borrowed rather than restated —
    duplicating the wording is how two settings start disagreeing about what a number
    is; `_int` wants a public name of its own, which is a change in `config`."""
    return _int(env, "CORA_PORT", DEFAULT_PORT, minimum=LOWEST_PORT)


def serve() -> None:
    config = Config.from_env()
    served = api(build(config), plugins=config.plugin_modules, ui=ui_path(os.environ))
    uvicorn.run(
        served,
        host=os.environ.get("CORA_HOST", "").strip() or DEFAULT_HOST,
        port=port(os.environ),
    )


if __name__ == "__main__":
    serve()
