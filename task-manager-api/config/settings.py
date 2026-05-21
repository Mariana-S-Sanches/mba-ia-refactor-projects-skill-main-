"""Configuração central, lida do ambiente."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass


def _bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    return raw.strip().lower() in {"1", "true", "yes", "on"} if raw else default


def _int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    return int(raw) if raw else default


class Settings:
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or "dev-only-secret-change-me"
    DEBUG: bool = _bool("DEBUG", False)
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = _int("PORT", 5000)

    DATABASE_URI: str = os.environ.get("DATABASE_URI", "sqlite:///tasks.db")

    JWT_EXP_MINUTES: int = _int("JWT_EXP_MINUTES", 60)

    SMTP_HOST: str = os.environ.get("SMTP_HOST", "")
    SMTP_PORT: int = _int("SMTP_PORT", 587)
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")

    DEFAULT_PAGE_SIZE: int = _int("DEFAULT_PAGE_SIZE", 50)
    MAX_PAGE_SIZE: int = _int("MAX_PAGE_SIZE", 100)


settings = Settings()
