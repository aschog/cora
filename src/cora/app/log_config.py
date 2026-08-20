"""Where cora's own logs go when `CORA_DEBUG` is set, and nowhere otherwise."""

import logging
from collections.abc import Callable
from pathlib import Path

PACKAGE_LOGGER = "cora"
DEBUG_HANDLER_NAME = "cora-debug"
FILE_HANDLER_NAME = "cora-debug-file"
LOG_FILE = ".cora/logs/cora.log"


def enable_debug_logs(enabled: bool, log_file: str | Path = LOG_FILE) -> None:
    """Attach cora's debug handlers — the stream and the file — once.

    Called twice on one logger it adds nothing: a frontend that reloads its script would
    otherwise log every line as many times as it has run.

    Args:
        enabled: Off means untouched. cora's logger carries no handler of its own then,
            so nothing below `warning` reaches the user's terminal.
        log_file: Where the file handler writes; its parent is created if it is missing.
    """
    if not enabled:
        return
    logger = logging.getLogger(PACKAGE_LOGGER)
    logger.setLevel(logging.DEBUG)
    _add_once(logger, DEBUG_HANDLER_NAME, _stream_handler)
    _add_once(logger, FILE_HANDLER_NAME, lambda: _file_handler(log_file))


def _add_once(
    logger: logging.Logger, name: str, make_handler: Callable[[], logging.Handler]
) -> None:
    if any(handler.name == name for handler in logger.handlers):
        return
    handler = make_handler()
    handler.name = name
    logger.addHandler(handler)


def _stream_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(name)s %(message)s"))
    return handler


def _file_handler(log_file: str | Path) -> logging.Handler:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    return handler
