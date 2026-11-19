"""Account credentials and unverified JWT metadata."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Awaitable, Callable
import math
import time

import jwt


@dataclass(frozen=True)
class TokenClaims:
    """Unverified metadata, never proof of identity or permissions."""

    user_id: int | None = None
    username: str | None = None
    role: str | None = None
    token_version: int | None = None
    exp: float | None = None
    iat: float | None = None

    @classmethod
    def from_token(cls, token: str) -> "TokenClaims | None":
        try:
            data = jwt.decode(token, options={"verify_signature": False})
        except (jwt.PyJWTError, ValueError, TypeError):
            return None

        def integer(key):
            value = data.get(key)
            return value if type(value) is int else None

        def string(key):
            value = data.get(key)
            return value if isinstance(value, str) else None

        def timestamp(key):
            value = data.get(key)
            if type(value) not in (int, float):
                return None
            try:
                value = float(value)
                if not math.isfinite(value):
                    return None
                datetime.fromtimestamp(value, timezone.utc)
                return value
            except (OverflowError, OSError, ValueError):
                return None

        return cls(
            integer("user_id"),
            string("username"),
            string("role"),
            integer("token_version"),
            timestamp("exp"),
            timestamp("iat"),
        )


@dataclass(frozen=True)
class SessionTokens:
    token: str = field(repr=False)
    refresh_token: str | None = field(default=None, repr=False)
    claims: TokenClaims | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", TokenClaims.from_token(self.token))

    @property
    def expires_at(self) -> datetime | None:
        """UTC expiration time, or None if unknown."""
        if self.claims is None or self.claims.exp is None:
            return None
        return datetime.fromtimestamp(self.claims.exp, timezone.utc)

    @property
    def issued_at(self) -> datetime | None:
        if self.claims is None or self.claims.iat is None:
            return None
        return datetime.fromtimestamp(self.claims.iat, timezone.utc)

    @property
    def expires_in(self) -> float | None:
        """Remaining seconds, clamped at zero; None if unknown."""
        if self.claims is None or self.claims.exp is None:
            return None
        return max(0.0, self.claims.exp - time.time())

    @property
    def is_expired(self) -> bool | None:
        remaining = self.expires_in
        return None if remaining is None else remaining <= 0


TokenRefreshCallback = Callable[[SessionTokens], Awaitable[None]]


class TokenPersistenceError(RuntimeError):
    """Rotated credentials are in memory but could not be persisted."""
