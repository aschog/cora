import importlib.util
import logging

import pytest
from streamlit.testing.v1 import AppTest

import cora.app.assembly as assembly
from cora.app.config import Config
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

WATCHER_LOGGER = "streamlit.watcher.local_sources_watcher"


@pytest.mark.integration
def test_shell_silences_watcher_import_noise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The watcher's hasattr probe trips transformers' lazy imports and logs
    a warning-level traceback per model; the shell must mute that logger."""
    monkeypatch.setattr(Config, "from_env", classmethod(lambda cls: None))
    monkeypatch.setattr(
        assembly,
        "build",
        lambda config: assembly.assemble(
            chat_model=ScriptedChatModel([]),
            embedder=FakeEmbedder(),
            retriever=FakeRetriever(),
            plugin=make_plugin(),
        ),
    )
    logging.getLogger(WATCHER_LOGGER).setLevel(logging.NOTSET)

    spec = importlib.util.find_spec("cora.app.ui.streamlit_app")
    assert spec is not None and spec.origin is not None
    at = AppTest.from_file(spec.origin)
    at.run()

    assert not at.exception
    assert logging.getLogger(WATCHER_LOGGER).level == logging.ERROR
