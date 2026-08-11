import importlib.util
import logging
from collections.abc import Iterator

import pytest
from streamlit.testing.v1 import AppTest

import cora.app.assembly as assembly
from cora.app.config import Config
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

WATCHER_LOGGER = "streamlit.watcher.local_sources_watcher"


@pytest.fixture
def watcher_logger() -> Iterator[logging.Logger]:
    logger = logging.getLogger(WATCHER_LOGGER)
    original_level = logger.level
    logger.setLevel(logging.NOTSET)
    yield logger
    logger.setLevel(original_level)


@pytest.mark.integration
def test_shell_silences_watcher_import_noise(
    monkeypatch: pytest.MonkeyPatch,
    watcher_logger: logging.Logger,
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
    spec = importlib.util.find_spec("cora.frontends.streamlit.streamlit_app")
    assert spec is not None and spec.origin is not None
    at = AppTest.from_file(spec.origin)
    at.run()

    assert not at.exception
    assert watcher_logger.level == logging.ERROR
