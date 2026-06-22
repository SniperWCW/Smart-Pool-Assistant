"""Dedicated file logging for Smart Pool Assistant diagnostics."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .const import DOMAIN

_LOGGER_NAME = "custom_components.smart_pool_assistant"
_HANDLER_MARKER = "_smart_pool_assistant_file_handler"
_LOG_FILE_NAME = "smart_pool_assistant.log"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5


def setup_file_logging(log_dir: str) -> str:
    """Attach a rotating DEBUG file handler to all integration loggers."""
    logger = logging.getLogger(_LOGGER_NAME)

    for handler in logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            logger.setLevel(logging.DEBUG)
            return str(getattr(handler, "baseFilename", ""))

    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    log_file = path / _LOG_FILE_NAME

    handler = RotatingFileHandler(
        log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    setattr(handler, _HANDLER_MARKER, True)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug(
        "%s file logging initialized: file=%s max_bytes=%s backups=%s",
        DOMAIN,
        log_file,
        _MAX_BYTES,
        _BACKUP_COUNT,
    )
    return str(log_file)
