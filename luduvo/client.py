"""Contains the main client class for interacting with the Luduvo API."""

import logging
from .utilities.classes import User
from .utilities.exceptions import NotFound, UserNotFound
from .utilities.url import URLGenerator
from .utilities.requests import Requests


logger = logging.getLogger("luduvo")


class Client:
    """Represents a Luduvo Client.

    Attributes:
        requests: The requests object, which is used to send requests to Luduvo endpoints.
        url_generator: The URL generator object, which is used to generate URLs to send requests to endpoints.
    """

    def __init__(self, base_url="luduvo.com"):
        """
        Args:
            base_url (str, optional): The base URL for the Luduvo API.
        """
        logger.debug("Initializing Client(base_url=%s)", base_url)

        self._url_generator: URLGenerator = URLGenerator(base_url=base_url)
        self._requests: Requests = Requests()

        self.url_generator: URLGenerator = self._url_generator
        self.requests: Requests = self._requests

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    # --------------------------
    # API Endpoints
    # --------------------------

    async def get_user(self, user_id: int) -> User:
        """
        Gets a user with the specified user ID.

        Arguments:
            user_id: A Luduvo user ID.

        Returns:
            A user object.
        """
        logger.debug(f"Fetching user with ID: {user_id}")
        try:
            user_response = await self._requests.get(
                url=self.url_generator.get_url("api", f"users/{user_id}/profile")
            )
        except NotFound as exception:
            logger.error(f"User not found: {user_id}")
            raise UserNotFound(
                message="Invalid user.", response=exception.response
            ) from None
        user_data = user_response.json()
        logger.debug(f"Successfully retrieved user data for ID: {user_id}")
        return User(client=self, data=user_data)
