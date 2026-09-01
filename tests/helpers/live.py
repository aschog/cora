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
    """Every store is redirected — documents, memory and conversations alike: an
    acceptance run that remembered things would otherwise write into whatever the
    developer is actually using, and the conversation path is the checkpointer's too, so
    a thread would carry yesterday's run into today's. The plugins are named by the
    caller rather than taken from the default set, which ships none: a training
    question needs a plugin that claims training as its subject."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is not set; the llm tier needs a real key")
    return dataclasses.replace(
        Config.from_env(),
        plugin_modules=plugins,
        scopes=scopes,
        db_path=str(store / "chroma"),
        memory_path=str(store / "memory.sqlite"),
        documents_path=str(store / "documents"),
        conversations_path=str(store / "conversations.sqlite"),
    )
