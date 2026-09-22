import dataclasses
import os
from pathlib import Path

import pytest

from cora.app.config import Config


def live_config(
    store: Path, plugins: tuple[str, ...], scopes: tuple[str, ...] = ()
) -> Config:
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
