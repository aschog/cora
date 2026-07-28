import logging
from collections.abc import Iterator

import pytest

from cora.app.log_config import enable_debug_logs


@pytest.fixture(autouse=True)
def clean_cora_logger() -> Iterator[logging.Logger]:
    logger = logging.getLogger("cora")
    level, handlers = logger.level, list(logger.handlers)
    logger.setLevel(logging.NOTSET)
    logger.handlers = []
    yield logger
    logger.setLevel(level)
    logger.handlers = handlers


def test_enable_debug_logs_puts_a_debug_handler_on_the_cora_logger(
    clean_cora_logger: logging.Logger,
) -> None:
    root_handlers = list(logging.getLogger().handlers)

    enable_debug_logs(True)

    assert clean_cora_logger.level == logging.DEBUG
    assert len(clean_cora_logger.handlers) == 1
    assert list(logging.getLogger().handlers) == root_handlers


def test_enable_debug_logs_adds_one_handler_however_often_it_runs(
    clean_cora_logger: logging.Logger,
) -> None:
    enable_debug_logs(True)
    enable_debug_logs(True)

    assert len(clean_cora_logger.handlers) == 1


def test_enable_debug_logs_leaves_logging_untouched_when_off(
    clean_cora_logger: logging.Logger,
) -> None:
    enable_debug_logs(False)

    assert clean_cora_logger.level == logging.NOTSET
    assert clean_cora_logger.handlers == []
