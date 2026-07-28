import logging

import pytest

from cora.app.log_config import enable_debug_logs


def test_enable_debug_logs_writes_the_lines_where_the_user_can_see_them(
    clean_cora_logger: logging.Logger, capsys: pytest.CaptureFixture[str]
) -> None:
    enable_debug_logs(True)

    logging.getLogger("cora.probe").debug("a line worth seeing")

    printed = capsys.readouterr().err
    assert "a line worth seeing" in printed
    assert "cora.probe" in printed


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
    root = logging.getLogger()
    saved_handlers, saved_level = list(root.handlers), root.level
    root.handlers = []  # basicConfig() is a no-op while root has handlers

    try:
        enable_debug_logs(False)

        assert root.handlers == []
        assert root.level == saved_level
    finally:
        root.handlers = saved_handlers

    assert clean_cora_logger.level == logging.NOTSET
    assert clean_cora_logger.handlers == []
