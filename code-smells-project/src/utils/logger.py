"""Configuração mínima de logging estruturado."""
from __future__ import annotations

import logging
import sys

from src.config.settings import settings


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # idempotente

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
