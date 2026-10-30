"""Password hashing and JWT helpers.

Uses the `bcrypt` library directly rather than passlib: passlib 1.7.4 (the
latest release) hard-crashes against bcrypt>=4.1 (it probes a removed
`bcrypt.__about__.__version__` attribute), and passlib has had no compatible
release since. bcrypt's own API is simple enough not to need the wrapper.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from ..config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_minutes: Optional[int] = None, session_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    if session_id is not None:
        to_encode["sid"] = session_id
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_claims(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM],
                          options={"require_exp": True, "require_sub": True})
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[str]:
    claims = decode_access_claims(token)
    return claims.get("sub") if claims else None
