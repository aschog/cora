import logging
import re
from pathlib import Path

from cora.app.log_config import (
    FILE_HANDLER_NAME,
    enable_debug_logs,
)


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


def test_enable_debug_logs_adds_each_handler_once_however_often_it_runs(
    clean_cora_logger: logging.Logger, tmp_path: Path
) -> None:
    log_file = tmp_path / "cora.log"

    enable_debug_logs(True, log_file=log_file)
    enable_debug_logs(True, log_file=log_file)

    file_handlers = [
        handler
        for handler in clean_cora_logger.handlers
        if handler.name == FILE_HANDLER_NAME
    ]
    assert len(file_handlers) == 1
