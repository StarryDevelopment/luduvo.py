"""Account session credentials. Never log or persist these in plaintext."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionTokens:
    token: str = field(repr=False)
    refresh_token: str | None = field(default=None, repr=False)
