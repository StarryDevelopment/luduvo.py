"""Experimental OAuth2 authorization-code integration for Luduvo.

The endpoint contract is based on community documentation, not a verified
official specification. Keep OAuth tokens separate from account credentials.
"""
import base64
import hashlib
import secrets
import time
from dataclasses import dataclass, field
from urllib.parse import urlencode

import httpx


class OAuth2Error(Exception):
    """OAuth flow failed without including sensitive response data."""


@dataclass(frozen=True)
class Authorization:
    url: str = field(repr=False)
    state: str = field(repr=False)
    verifier: str = field(repr=False)
    expires_at: float


@dataclass(frozen=True)
class OAuthToken:
    access_token: str = field(repr=False)
    token_type: str = "Bearer"
    expires_in: int | None = None
    scope: str | None = None
    refresh_token: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class OAuthUser:
    id: int
    username: str
    sub: str
    display_name: str | None = None
    avatar_url: str | None = None
    created_at: int | None = None


class OAuth2Client:
    """Independent async OAuth client; state storage belongs to the application."""

    def __init__(self, client_id: str, redirect_uri: str, *,
                 client_secret: str | None = None, timeout: float = 15,
                 authorization_url: str = "https://luduvo.com/oauth/authorize",
                 transport: httpx.AsyncBaseTransport | None = None):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self._client_secret = client_secret
        self.authorization_url = authorization_url
        self._session = httpx.AsyncClient(timeout=timeout, transport=transport,
                                          follow_redirects=False)

    def authorize(self, *, scope: str = "identify", ttl: int = 300) -> Authorization:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        verifier = secrets.token_urlsafe(64)
        state = secrets.token_urlsafe(32)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        query = urlencode({
            "client_id": self.client_id, "redirect_uri": self.redirect_uri,
            "response_type": "code", "scope": scope, "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256",
        })
        return Authorization(f"{self.authorization_url}?{query}", state, verifier,
                             time.time() + ttl)

    async def exchange(self, code: str, state: str, authorization: Authorization) -> OAuthToken:
        """Validate callback state and exchange its code.

        The caller must atomically consume the stored authorization session and
        bind it to the initiating user before invoking this method.
        """
        if time.time() >= authorization.expires_at:
            raise OAuth2Error("Authorization session expired")
        if not state or not secrets.compare_digest(state.encode("utf-8"), authorization.state.encode("utf-8")):
            raise OAuth2Error("Invalid authorization state")
        if not code:
            raise OAuth2Error("Missing authorization code")
        body = {
            "grant_type": "authorization_code", "client_id": self.client_id,
            "redirect_uri": self.redirect_uri, "code": code,
            "code_verifier": authorization.verifier,
        }
        if self._client_secret is not None:
            body["client_secret"] = self._client_secret
        response = await self._session.post("https://api.luduvo.com/oauth/token", json=body)
        data = self._decode(response)
        token = data.get("access_token")
        if not isinstance(token, str) or not token:
            raise OAuth2Error("Missing OAuth access token")
        token_type = data.get("token_type", "Bearer")
        if not isinstance(token_type, str) or token_type.lower() != "bearer":
            raise OAuth2Error("Unsupported OAuth token type")
        return OAuthToken(token, token_type, data.get("expires_in"),
                          data.get("scope"), data.get("refresh_token"))

    async def userinfo(self, token: OAuthToken | str) -> OAuthUser:
        value = token.access_token if isinstance(token, OAuthToken) else token
        response = await self._session.get("https://api.luduvo.com/oauth/userinfo",
                                           headers={"Authorization": f"Bearer {value}"})
        data = self._decode(response)
        try:
            user_id = int(data["id"])
            subject = str(data["sub"])
            if subject != str(user_id):
                raise ValueError("Inconsistent subject")
            return OAuthUser(user_id, data["username"], subject,
                             data.get("display_name"), data.get("avatar_url"),
                             data.get("created_at"))
        except (KeyError, ValueError, TypeError):
            raise OAuth2Error("Invalid OAuth userinfo response") from None

    @staticmethod
    def _decode(response):
        if not response.is_success:
            raise OAuth2Error(f"OAuth request failed ({response.status_code})")
        try:
            data = response.json()
        except ValueError:
            raise OAuth2Error("Invalid OAuth response") from None
        if not isinstance(data, dict) or data.get("error"):
            raise OAuth2Error("Invalid OAuth response")
        return data

    async def close(self):
        await self._session.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
