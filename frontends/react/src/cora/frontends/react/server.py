"""The process the deployment runs: cora assembled once, served over HTTP.

The build it serves is looked for beside the package rather than shipped inside it —
`ui/dist` is Vite's output, not a Python module. Nothing is mounted when it is absent,
which is a dev machine running the page on Vite instead.
"""

import os
import pathlib

import uvicorn

from cora.app.assembly import build
from cora.app.config import Config
from cora.frontends.react.api import api

DEFAULT_UI = pathlib.Path(__file__).resolve().parents[4] / "ui" / "dist"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def serve() -> None:
    config = Config.from_env()
    served = api(
        build(config),
        plugins=config.plugin_modules,
        ui=pathlib.Path(os.environ.get("CORA_UI_PATH", "").strip() or DEFAULT_UI),
    )
    uvicorn.run(
        served,
        host=os.environ.get("CORA_HOST", "").strip() or DEFAULT_HOST,
        port=int(os.environ.get("CORA_PORT", "").strip() or DEFAULT_PORT),
    )


if __name__ == "__main__":
    serve()
