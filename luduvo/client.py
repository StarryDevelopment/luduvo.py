"""Contains the main client class for interacting with the Luduvo API."""

import logging
from .classes import User, PartialUser, Place
from .utilities.exceptions import NotFound, UserNotFound, PlaceNotFound
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
                url=self.url_generator.get_url(f"users/{user_id}/profile", "api")
            )
        except NotFound as exception:
            logger.error(f"User not found: {user_id}")
            raise UserNotFound(
                message="Invalid user.", response=exception.response
            ) from None
        user_data = user_response.json()
        logger.debug(f"Successfully retrieved user data for ID: {user_id}")
        return User(client=self, data=user_data)

    async def get_user_by_username(
        self, username: str, expand: bool = True
    ) -> User | PartialUser:
        """
        Gets a user with the specified username.

        Arguments:
            username: A Luduvo username.
            expand: Whether to return a User (2 requests) rather than a PartialUser (1 request)

        Returns:
            A User or PartialUser depending on the expand argument.
        """
        logger.debug(f"Fetching user with username: {username}")
        try:
            user_response = await self._requests.get(
                url=self.url_generator.get_url(f"users?q={username}", "api")
            )
        except NotFound as exception:
            logger.error(f"User not found: {username}")
            raise UserNotFound(
                message="Invalid user.", response=exception.response
            ) from None
        user_data = user_response.json()
        if len(user_data) == 0:
            logger.error(f"User not found: {username}")
            raise UserNotFound(message="Invalid user.")
        user_info = user_data[0]
        if expand:
            logger.debug(f"Expanding user data for username: {username}")
            return await self.get_user(user_info["id"])
        return PartialUser(client=self, data=user_info)

    async def get_place(self, place_id: int) -> Place:
        """
        Gets a place with the specified place ID.

        Arguments:
            place_id: A Luduvo place ID.

        Returns:
            A place object.
        """
        logger.debug(f"Fetching place with ID: {place_id}")
        try:
            place_response = await self._requests.get(
                url=self.url_generator.get_url(f"places/{place_id}", "api")
            )
        except NotFound as exception:
            logger.error(f"Place not found: {place_id}")
            raise PlaceNotFound(
                message="Invalid place.", response=exception.response
            ) from None
        place_data = place_response.json()
        logger.debug(f"Successfully retrieved place data for ID: {place_id}")
        return Place(client=self, data=place_data)

    async def close(self):
        """
        Closes the client session.
        """
        await self._requests.session.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
