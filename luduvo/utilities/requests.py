"""

This module contains classes used internally for sending requests to Luduvo endpoints.

"""

from __future__ import annotations
import asyncio
from ..session import SessionTokens
import jwt
import datetime
import time
import math
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit


from json import JSONDecodeError

from httpx import AsyncClient, Response

from .exceptions import get_exception_from_status_code
import logging

logger = logging.getLogger(__name__)


class CleanAsyncClient(AsyncClient):
    """
    This is a clean-on-delete version of httpx.AsyncClient.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Requests:
    """
    A special request object that implements special functionality required to connect to some Luduvo endpoints.

    Attributes:
        session: Base session object to use when sending requests.
    """

    def __init__(
        self,
        *,
        session: CleanAsyncClient | None = None,
        base_url: str = "luduvo.com",
        token: str | None = None,
        refresh_token: str | None = None,
        timeout: float = 15.0,
        max_concurrency: int = 4,
        max_retries: int = 2,
        max_retry_after: float = 60.0,
    ):
        """
        Arguments:
            session: A custom session object to use for sending requests, compatible with httpx.AsyncClient.
        """
        self.session: CleanAsyncClient
        self.authenticated: bool = False

        if max_concurrency < 1 or max_retries < 0 or not math.isfinite(max_retry_after) or max_retry_after < 0:
            raise ValueError("Invalid transport limits")
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._max_retries = max_retries
        self._max_retry_after = max_retry_after
        self._blocked_until = 0.0
        self._timeout = timeout

        if session is None:
            self.session = CleanAsyncClient(timeout=timeout)
        else:
            self.session = session

        self.base_url = base_url
        self._auth_lock = asyncio.Lock()
        self._tokens = None
        self._expires_at = None
        if refresh_token and not token:
            raise ValueError("An access token is required with a refresh token")
        if token:
            self._set_tokens(token, refresh_token)
        self.session.headers["User-Agent"] = "Python/luduvo.py"

    @property
    def tokens(self) -> SessionTokens | None:
        """Return the latest token pair. Treat both values as secrets."""
        return self._tokens

    def _set_tokens(self, token, refresh):
        if not isinstance(token, str) or not token:
            raise ValueError("Missing access token")
        if refresh is not None and (not isinstance(refresh, str) or not refresh):
            raise ValueError("Invalid refresh token")
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._tokens = SessionTokens(token, refresh)
        self.authenticated = True
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
            self._expires_at = float(claims["exp"])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            self._expires_at = None

    async def _refresh(self):
        if self._tokens is None or not self._tokens.refresh_token:
            raise ValueError("No refresh token configured")
        response = await self._send(
            "POST", f"https://api.{self.base_url}/auth/refresh",
            headers={"Authorization": ""},
            json={"refresh_token": self._tokens.refresh_token},
        )
        data = response.json()
        if not data.get("refresh_token"):
            raise ValueError("Refresh response is missing refresh_token")
        self._set_tokens(data.get("token"), data["refresh_token"])
        return self._tokens

    async def refresh(self):
        """Explicitly refresh an authorized session."""
        async with self._auth_lock:
            return await self._refresh()

    async def ensure_authenticated(self):
        """Refresh an expiring session before a request."""
        async with self._auth_lock:
            if (self._tokens and self._tokens.refresh_token
                    and self._expires_at is not None
                    and self._expires_at <= time.time() + 10):
                await self._refresh()

    async def close(self):
        self._tokens = None
        self._expires_at = None
        self.authenticated = False
        self.session.headers.pop("Authorization", None)
        await self.session.aclose()

    async def request(self, method: str, *args, **kwargs) -> Response:
        await self.ensure_authenticated()
        return await self._send(method, *args, **kwargs)

    async def _send(self, method: str, *args, **kwargs) -> Response:
        """
        Arguments:
            method: The request method.

        Returns:
            An HTTP response.
        """

        url = (
            kwargs.get("url") if "url" in kwargs else (args[0] if args else "<unknown>")
        )
        target = urlsplit(str(url))
        if target.scheme != "https" or target.netloc != f"api.{self.base_url}":
            raise ValueError("Requests must target the configured HTTPS API origin")
        if kwargs.get("follow_redirects"):
            raise ValueError("Automatic redirects are not supported")
        kwargs["follow_redirects"] = False
        kwargs.setdefault("timeout", self._timeout)
        method = method.upper()
        logger.debug("Sending HTTP request: %s", method)

        for attempt in range(self._max_retries + 1):
            async with self._semaphore:
                delay = self._blocked_until - time.monotonic()
                if delay > self._max_retry_after:
                    raise self._last_rate_limit
                if delay > 0:
                    await asyncio.sleep(delay)
                response = await self.session.request(method, *args, **kwargs)
                if response.status_code == 429:
                    delay = self._retry_delay(response, attempt)
                    self._blocked_until = max(self._blocked_until, time.monotonic() + delay)
                    self._last_rate_limit = get_exception_from_status_code(429)(response=response)
            if method not in {"GET", "HEAD"} or attempt == self._max_retries:
                break
            if response.status_code == 429:
                if delay > self._max_retry_after:
                    break
                continue
            if response.status_code in {502, 503, 504}:
                delay = self._retry_delay(response, attempt)
                if delay > self._max_retry_after:
                    break
                await asyncio.sleep(delay)
                continue
            break

        method = method.lower()

        if response.is_error:
            # Something went wrong, parse an error
            logger.error("HTTP request failed: %s", response.status_code)

            content_type = response.headers.get("Content-Type")
            errors = None
            if content_type and content_type.startswith("application/json"):
                data = None
                try:
                    data = response.json()
                except JSONDecodeError:
                    logger.debug("Failed to decode JSON error response")
                errors = data.get("errors") if isinstance(data, dict) else None

            exception = get_exception_from_status_code(response.status_code)(
                response=response, errors=errors
            )
            raise exception
        else:
            logger.debug("HTTP request succeeded: %s", response.status_code)
            return response

    @staticmethod
    def _retry_delay(response, attempt):
        value = response.headers.get("Retry-After")
        if value is not None:
            try:
                seconds = float(value)
                if math.isfinite(seconds):
                    return max(0.0, seconds)
            except ValueError:
                try:
                    date = parsedate_to_datetime(value)
                    return max(0.0, (date - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
                except (ValueError, TypeError, OverflowError):
                    pass
        return min(2 ** attempt, 30)

    async def get(self, *args, **kwargs) -> Response:
        """
        Sends a GET request.

        Returns:
            An HTTP response.
        """

        return await self.request("GET", *args, **kwargs)

    async def post(self, *args, **kwargs) -> Response:
        """
        Sends a POST request.

        Returns:
            An HTTP response.
        """

        return await self.request("POST", *args, **kwargs)

    async def put(self, *args, **kwargs) -> Response:
        """
        Sends a PUT request.

        Returns:
            An HTTP response.
        """

        return await self.request("PUT", *args, **kwargs)

    async def patch(self, *args, **kwargs) -> Response:
        """
        Sends a PATCH request.

        Returns:
            An HTTP response.
        """

        return await self.request("PATCH", *args, **kwargs)

    async def delete(self, *args, **kwargs) -> Response:
        """
        Sends a DELETE request.

        Returns:
            An HTTP response.
        """

        return await self.request("DELETE", *args, **kwargs)
