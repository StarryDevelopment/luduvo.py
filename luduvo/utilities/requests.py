"""

This module contains classes used internally for sending requests to Luduvo endpoints.

"""

from __future__ import annotations

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
        # ty:ignore[invalid-parameter-default]
        session: CleanAsyncClient = None,
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

        # self.session.headers["User-Agent"] = "Python/luduvo-api-wrapper"
        # self.session.headers["Referer"] = "luduvo.com"

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
