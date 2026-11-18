"""

This module contains classes used internally for sending requests to Luduvo endpoints.

"""

from __future__ import annotations
import asyncio
import jwt
import datetime


from json import JSONDecodeError

from httpx import AsyncClient, Response

from .exceptions import get_exception_from_status_code
import logging

logger = logging.getLogger(__name__)


class CleanAsyncClient(AsyncClient):
    """
    This is a clean-on-delete version of httpx.AsyncClient.
    """

    def __init__(self):
        super().__init__()


class Requests:
    """
    A special request object that implements special functionality required to connect to some Luduvo endpoints.

    Attributes:
        session: Base session object to use when sending requests.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        session: CleanAsyncClient | None = None,
        base_url: str = "luduvo.com",
        token: str | None = None,
    ):
        """
        Arguments:
            session: A custom session object to use for sending requests, compatible with httpx.AsyncClient.
        """
        self.session: CleanAsyncClient
        self.authenticated: bool = False

        if session is None:
            self.session = CleanAsyncClient()
        else:
            self.session = session

        if bool(username) != bool(password):
            raise ValueError("Both username and password are required")
        if token and username:
            raise ValueError("Choose credentials or token, not both")
        self.base_url = base_url
        self._auth_lock = asyncio.Lock()
        self._credentials = (username, password) if username and password else None
        self._refresh_token = None
        self._expires_at = None
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
            self.authenticated = True
        self.session.headers["User-Agent"] = "Python/luduvo.py"

    async def authenticate(self, username: str, password: str) -> bool:
        """Log in without blocking the event loop."""
        if not username or not password:
            raise ValueError("Both username and password are required")
        async with self._auth_lock:
            await self._login(username, password)
        return True

    async def _login(self, username, password):
        response = await self._send("POST", self._auth_url("login"),
                                    json={"identifier": username, "password": password})
        self._set_tokens(response.json())
        self._credentials = None

    def _auth_url(self, action):
        return f"https://api.{self.base_url}/auth/{action}"

    def _set_tokens(self, data):
        token, refresh = data.get("token"), data.get("refresh_token")
        if not isinstance(token, str) or not token or not isinstance(refresh, str) or not refresh:
            raise ValueError("Authentication response is missing tokens")
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._refresh_token = refresh
        self.authenticated = True
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
            self._expires_at = float(claims["exp"])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            self._expires_at = None

    async def ensure_authenticated(self):
        """Initialize deferred credentials and refresh expiring tokens on demand."""
        async with self._auth_lock:
            if self._credentials is not None:
                await self._login(*self._credentials)
            elif (self._refresh_token and self._expires_at is not None
                  and self._expires_at <= datetime.datetime.now(datetime.timezone.utc).timestamp() + 10):
                response = await self._send("POST", self._auth_url("refresh"),
                                            json={"refresh_token": self._refresh_token})
                self._set_tokens(response.json())

    async def close(self):
        self._credentials = None
        self._refresh_token = None
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
        logger.debug("Sending HTTP request: %s %s", method.upper(), url)

        response = await self.session.request(method, *args, **kwargs)

        method = method.lower()

        if response.is_error:
            # Something went wrong, parse an error
            logger.error(
                "HTTP request failed: %s %s %s",
                response.status_code,
                response.reason_phrase,
                response.url,
            )

            content_type = response.headers.get("Content-Type")
            errors = None
            if content_type and content_type.startswith("application/json"):
                data = None
                try:
                    data = response.json()
                except JSONDecodeError:
                    logger.debug(
                        "Failed to decode JSON error response from %s",
                        response.url,
                    )
                errors = data.get("errors") if isinstance(data, dict) else None
                if errors:
                    logger.debug("Parsed error payload: %s", errors)

            exception = get_exception_from_status_code(response.status_code)(
                response=response, errors=errors
            )
            raise exception
        else:
            logger.debug(
                "HTTP request succeeded: %s %s",
                response.status_code,
                response.url,
            )
            return response

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
        Sends a PATCH request.

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
