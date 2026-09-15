"""The configuration the `llm` tier runs under: the shipped one, pointed at its own
stores. Here rather than in a suite because two suites in that tier need it, and a test
module is not importable from another under importlib mode."""

import dataclasses
import os
from pathlib import Path

import pytest

from cora.app.config import Config


def live_config(
    store: Path, plugins: tuple[str, ...], scopes: tuple[str, ...] = ()
) -> Config:
    """Every location is redirected: the database, the documents beside it, and the
    folder plugins are dropped into. An acceptance run that remembered things would
    otherwise write into whatever the developer is actually using, and the database is
    the checkpointer's too, so a thread would carry yesterday's run into today's.

    The folder for one more reason: a deployment that linked this repo's plugins into
    `.cora/plugins` carries them by *that* route, and naming one as a module as well is
    two plugins with one name, which cora refuses. The tier says which plugins it runs.
    """
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is not set; the llm tier needs a real key")
    return dataclasses.replace(
        Config.from_env(),
        plugin_modules=plugins,
        scopes=scopes,
        db_path=str(store / "cora.sqlite"),
        documents_path=str(store / "documents"),
        plugins_path=str(store / "plugins"),
    )
