"""Hashing de senha (bcrypt) + JWT real."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config.settings import settings


# ---- senha ---------------------------------------------------------------

def hash_password(plain: str) -> str:
    if not plain:
        raise ValueError("Senha não pode ser vazia")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---- JWT -----------------------------------------------------------------

def create_token(user_id: int, role: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXP_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
