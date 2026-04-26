"""

This module contains classes used internally for sending requests to Luduvo endpoints.

"""

from __future__ import annotations
import httpx
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

        if username and password:
            logger.debug(
                "Initializing authenticated Requests instance with username: %s",
                username,
            )
            self.authenticated = self.authenticate(username=username, password=password)
        else:
            self.authenticated = False
            logger.debug("Initialized unauthenticated Requests instance")

        self.session.headers["User-Agent"] = "Python/luduvo.py"

    async def _authenticate_with_refresh_token(
        self, refresh_token: str, delay: int = 0
    ):
        """
        Internal method to re-authenticate the client using a refresh token.

        Arguments:
            refresh_token: The refresh token to use for re-authentication.
            delay: The delay in seconds before attempting re-authentication.
        """
        if delay > 0:
            logger.debug(
                "Waiting for %d minutes before attempting re-authentication with refresh token",
                delay / 60,
            )
            await asyncio.sleep(delay)
        logger.debug("Attempting re-authentication with refresh token")
        try:
            resp = httpx.request(
                "POST",
                "https://api.luduvo.com/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            if resp.is_error:
                logger.error(
                    "Re-authentication with refresh token failed: %s %s",
                    resp.status_code,
                    resp.reason_phrase,
                )
                raise get_exception_from_status_code(resp.status_code)(response=resp)
            if "token" not in resp.json() and "refresh_token" not in resp.json():
                raise Exception(
                    "Re-authentication failed: No token or refresh_token in response"
                )
            new_token = resp.json()["token"]
            new_refresh_token = resp.json()["refresh_token"]

            decoded_token = jwt.decode(new_token, options={"verify_signature": False})
            exp = decoded_token.get("exp")
            iat = decoded_token.get("iat")
            if exp and iat:
                logger.debug(
                    "Re-authenticated successfully with refresh token (Token expires at %s, issued at %s)",
                    datetime.datetime.fromtimestamp(exp),
                    datetime.datetime.fromtimestamp(iat),
                )
                sleep_time = (
                    (exp - iat) - 3600  # Schedule 1 hour before expiration
                )
                logger.debug(
                    "Scheduling next re-authentication in %d minutes",
                    sleep_time // 60,
                )
                asyncio.create_task(
                    self._authenticate_with_refresh_token(
                        refresh_token=new_refresh_token, delay=sleep_time
                    )
                )

            self.session.headers["Authorization"] = f"Bearer {new_token}"
        except Exception as e:
            logger.error("Failed to re-authenticate with refresh token: %s", str(e))
            raise

    def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> bool:
        """
        Authenticates the client with the provided username and password.

        Arguments:
            username: The username to authenticate with.
            password: The password to authenticate with.
        """

        if not (username and password):
            raise ValueError(
                "Username and password must be provided for authentication"
            )

        resp = httpx.request(
            "POST",
            "https://api.luduvo.com/auth/login",
            json={"identifier": username, "password": password},
        )
        if resp.is_error:
            if resp.status_code == 401:
                raise Exception("Authentication failed: Invalid username or password")
            raise get_exception_from_status_code(resp.status_code)(response=resp)
        if "token" not in resp.json() and "refresh_token" not in resp.json():
            raise Exception(
                "Authentication failed: No token or refresh_token in response"
            )
        token = resp.json()["token"]
        refresh_token = resp.json()["refresh_token"]

        # Decode the token to extract user information
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        exp = decoded_token.get("exp")
        iat = decoded_token.get("iat")
        if exp and iat:
            logger.debug(
                "Authenticated successfully with username: %s (Token expires at %s, issued at %s)",
                username,
                datetime.datetime.fromtimestamp(exp),
                datetime.datetime.fromtimestamp(iat),
            )
            sleep_time = (exp - iat) - 3600  # Schedule 1 hour before expiration
            logger.debug(
                "Scheduling re-authentication in %d minutes",
                sleep_time // 60,
            )
            asyncio.create_task(
                self._authenticate_with_refresh_token(
                    refresh_token=refresh_token, delay=sleep_time
                )
            )

        self.session.headers["Authorization"] = f"Bearer {token}"
        check_resp = httpx.get(
            "https://api.luduvo.com/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        if check_resp.is_error:
            raise get_exception_from_status_code(check_resp.status_code)(
                response=check_resp
            )
        if check_resp.json().get("user_id") is None:
            raise Exception("Authentication failed: No user ID in check response")
        if check_resp.json().get("username") != username:
            raise Exception(
                "Authentication failed: Check response username did not match provided username"
            )
        logger.debug(
            "Authenticated successfully with username: %s (ID: %s)",
            username,
            check_resp.json().get("user_id"),
        )
        self.authenticated = True
        return True

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
