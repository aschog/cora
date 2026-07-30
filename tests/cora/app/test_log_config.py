import logging
import re
from pathlib import Path

import pytest

from cora.app.log_config import FILE_HANDLER_NAME, enable_debug_logs


def test_enable_debug_logs_writes_the_lines_where_the_user_can_see_them(
    clean_cora_logger: logging.Logger, capsys: pytest.CaptureFixture[str]
) -> None:
    enable_debug_logs(True)

    logging.getLogger("cora.probe").debug("a line worth seeing")

    printed = capsys.readouterr().err
    assert "a line worth seeing" in printed
    assert "cora.probe" in printed


def test_enable_debug_logs_writes_a_timestamped_line_to_a_file(
    clean_cora_logger: logging.Logger, tmp_path: Path
) -> None:
    log_file = tmp_path / "logs" / "cora.log"

    enable_debug_logs(True, log_file=log_file)
    logging.getLogger("cora.probe").debug("a line worth keeping")

    written = log_file.read_text()
    assert "a line worth keeping" in written
    assert "cora.probe" in written
    assert "DEBUG" in written
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", written)


def test_enable_debug_logs_off_creates_no_file_or_directory(
    clean_cora_logger: logging.Logger, tmp_path: Path
) -> None:
    log_file = tmp_path / "logs" / "cora.log"

    enable_debug_logs(False, log_file=log_file)

    assert not log_file.exists()
    assert not log_file.parent.exists()
    assert not any(
        handler.name == FILE_HANDLER_NAME for handler in clean_cora_logger.handlers
    )


def test_enable_debug_logs_puts_debug_handlers_on_the_cora_logger(
    clean_cora_logger: logging.Logger, tmp_path: Path
) -> None:
    root_handlers = list(logging.getLogger().handlers)

    enable_debug_logs(True, log_file=tmp_path / "cora.log")

    assert clean_cora_logger.level == logging.DEBUG
    assert len(clean_cora_logger.handlers) == 2
    assert list(logging.getLogger().handlers) == root_handlers


def test_enable_debug_logs_adds_each_handler_once_however_often_it_runs(
    clean_cora_logger: logging.Logger, tmp_path: Path
) -> None:
    log_file = tmp_path / "cora.log"

    enable_debug_logs(True, log_file=log_file)
    enable_debug_logs(True, log_file=log_file)

    assert len(clean_cora_logger.handlers) == 2


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
