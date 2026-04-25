"""

This module contains classes used internally for sending requests to Luduvo endpoints.

"""

from __future__ import annotations
import httpx
import asyncio



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
    ):
        """
        Arguments:
            session: A custom session object to use for sending requests, compatible with httpx.AsyncClient.
        """
        self.session: CleanAsyncClient

        if session is None:
            self.session = CleanAsyncClient()
        else:
            self.session = session

        if username and password:
            self.authenticate(username, password)
            asyncio.create_task(self._authenticate_loop(username, password))
        else:
            self.authenticated = False
            logger.debug("Initialized unauthenticated Requests instance")

        self.session.headers["User-Agent"] = "Python/luduvo.py"

    async def _authenticate_loop(
        self, username: str, password: str, sleep_time: int = 3600
    ):
        """
        An internal loop that re-authenticates the client every 60 minutes.

        Arguments:
            username: The username to authenticate with.
            password: The password to authenticate with.
            sleep_time: The time to sleep between re-authentications.
        """
        while True:
            logger.debug(
                "Sleeping for %d minutes before re-authentication", sleep_time // 60
            )
            await asyncio.sleep(sleep_time)
            logger.debug("Re-authenticating with username: %s", username)
            self.authenticate(username, password)

    def authenticate(self, username: str, password: str):
        """
        Authenticates the client with the provided username and password.

        Arguments:
            username: The username to authenticate with.
            password: The password to authenticate with.
        """

        resp = httpx.request(
            "POST",
            "https://api.luduvo.com/auth/login",
            json={"identifier": username, "password": password},
        )
        if resp.is_error:
            logger.error("Authentication failed for username: %s", username)
            if resp.status_code == 401:
                raise Exception("Authentication failed: Invalid username or password")
            raise get_exception_from_status_code(resp.status_code)(response=resp)
        if "token" not in resp.json() and "refresh_token" not in resp.json():
            logger.error(
                "Authentication response did not contain token or refresh_token for username: %s",
                username,
            )
            raise Exception(
                "Authentication failed: No token or refresh_token in response"
            )
        token = resp.json()["token"]

        self.session.headers["Authorization"] = f"Bearer {token}"
        check_resp = httpx.get(
            "https://api.luduvo.com/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        if check_resp.is_error:
            logger.error("Authentication check failed for username: %s", username)
            raise get_exception_from_status_code(check_resp.status_code)(
                response=check_resp
            )
        if check_resp.json().get("user_id") is None:
            logger.error(
                "Authentication check response did not contain user ID for username: %s",
                username,
            )
            raise Exception("Authentication failed: No user ID in check response")
        if check_resp.json().get("username") != username:
            logger.error(
                "Authentication check response username did not match provided username for username: %s",
                username,
            )
            raise Exception(
                "Authentication failed: Check response username did not match provided username"
            )
        self.authenticated = True
        logger.debug(
            "Authenticated successfully with username: %s (ID: %s)",
            username,
            check_resp.json().get("user_id"),
        )

    async def request(self, method: str, *args, **kwargs) -> Response:
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
                errors = data and data.get("errors")
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
