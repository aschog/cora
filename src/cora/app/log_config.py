import logging

PACKAGE_LOGGER = "cora"
DEBUG_HANDLER_NAME = "cora-debug"


def enable_debug_logs(enabled: bool) -> None:
    if not enabled:
        return
    logger = logging.getLogger(PACKAGE_LOGGER)
    logger.setLevel(logging.DEBUG)
    if any(handler.name == DEBUG_HANDLER_NAME for handler in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler.name = DEBUG_HANDLER_NAME
    handler.setFormatter(logging.Formatter("%(name)s %(message)s"))
    logger.addHandler(handler)
