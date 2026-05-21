"""Configuração central — lê do ambiente e falha cedo se algo obrigatório faltar."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:  # python-dotenv é opcional em produção (var vem do orquestrador)
    pass


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(
            f"Environment variable {key} is required. "
            f"Copy .env.example to .env and fill it out."
        )
    return value


def _bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return int(raw)


class Settings:
    # Em desenvolvimento, aceitamos um fallback inseguro para facilitar o boot
    # local; em produção exigimos a env var.
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or "dev-only-secret-change-me"
    DEBUG: bool = _bool("DEBUG", False)
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "loja.db")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = _int("PORT", 5000)
    DEFAULT_PAGE_SIZE: int = _int("DEFAULT_PAGE_SIZE", 50)
    MAX_PAGE_SIZE: int = _int("MAX_PAGE_SIZE", 100)


settings = Settings()
