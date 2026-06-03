"""Contains the main client class for interacting with the Luduvo API."""

import logging
from .classes import User, Place, Group
from .utilities.exceptions import NotFound, UserNotFound, PlaceNotFound, GroupNotFound
from .utilities.url import URLGenerator
from .utilities.requests import Requests


logger = logging.getLogger("luduvo")


class Client:
    """Represents a Luduvo API client.

    This class is the main entry point for interacting with the Luduvo API.
    It manages authentication, HTTP requests, and access to high-level
    resources such as users, places, and groups.

    Attributes:
        requests: The HTTP request handler used to communicate with API endpoints.
        url_generator: Utility used to construct API URLs for requests.
        authenticated: Whether the client is currently authenticated.
    """

    def __init__(self, username=None, password=None, base_url="luduvo.com"):
        """
        Initialize a Luduvo Client instance.

        Args:
            username (str, optional): Username used for authentication.
            password (str, optional): Password used for authentication.
            base_url (str, optional): Base URL for the Luduvo API.

        Example:
            ```python
            client = Client(username="john", password="secret")
            ```
        """
        logger.debug("Initializing Client(base_url=%s)", base_url)

        self._url_generator: URLGenerator = URLGenerator(base_url=base_url)

        if username and password:
            logger.debug("Authenticating with username: %s", username)
            self._requests = Requests(username=username, password=password)
        else:
            self._requests = Requests()

        self.url_generator: URLGenerator = self._url_generator
        self.requests: Requests = self._requests

        self.authenticated: bool = self.requests.authenticated

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    # --------------------------
    # API Endpoints
    # --------------------------

    async def get_user(self, user_id: int) -> User:
        """
        Retrieve a user by their unique user ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: A fully populated User object.

        Raises:
            UserNotFound: If the user does not exist.

        Example:
            ```python
            user = await client.get_user(123)
            print(user.username)
            ```
        """
        logger.debug(f"Fetching user with ID: {user_id}")
        try:
            user_response = await self._requests.get(
                url=self.url_generator.get_url(f"users/{user_id}/profile", "api")
            )
        except NotFound as exception:
            raise UserNotFound(
                message="Invalid user.", response=exception.response
            ) from None

        user_data = user_response.json()
        logger.debug(f"Successfully retrieved user data for ID: {user_id}")
        return User(client=self, data=user_data)

    async def get_user_by_username(self, username: str, expand: bool = True) -> User:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username to search for.
            expand (bool, optional): Deprecated. Whether to return a full User object or a PartialUser.
                Defaults to True. This parameter is ignored as of v1.2.0 and will always return a full User object.

        Returns:
            User: The requested user representation.

        Raises:
            UserNotFound: If no user matches the given username.

        Example:
            ```python
            user = await client.get_user_by_username("john")
            print(user.id)
            ```
        """
        logger.debug(f"Fetching user with username: {username}")
        try:
            user_response = await self._requests.get(
                url=self.url_generator.get_url(
                    f"users/by-username/{username}/profile", "api"
                )
            )
        except NotFound as exception:
            logger.error(f"User not found: {username}")
            raise UserNotFound(
                message="Invalid user.", response=exception.response
            ) from None

        user_data = user_response.json()
        if len(user_data) == 0 or "user_id" not in user_data:
            raise UserNotFound(message="Invalid user.")

        return User(client=self, data=user_data)

    async def get_authenticated_user(self) -> User:
        """
        Retrieve the currently authenticated user.

        Returns:
            User: The authenticated user's full profile.

        Raises:
            Exception: If the client is not authenticated.
            UserNotFound: If the authenticated user cannot be retrieved.

        Example:
            ```python
            me = await client.get_authenticated_user()
            print(me.username)
            ```
        """
        if not self.authenticated:
            raise Exception("Client is not authenticated.")

        logger.debug("Fetching authenticated user profile")
        try:
            user_response = await self._requests.get(
                url=self.url_generator.get_url("me/profile")
            )
        except NotFound as exception:
            logger.error("Authenticated user profile not found")
            raise UserNotFound(
                message="Authenticated user not found.", response=exception.response
            ) from None

        user_data = user_response.json()
        logger.debug(
            f"Successfully retrieved authenticated user data (ID: {user_data.get('user_id')})"
        )
        return User(client=self, data=user_data)

    async def get_place(self, place_id: int) -> Place:
        """
        Retrieve a place by its unique place ID.

        Args:
            place_id (int): The ID of the place to retrieve.

        Returns:
            Place: A Place object representing the requested place.

        Raises:
            PlaceNotFound: If the place does not exist.

        Example:
            ```python
            place = await client.get_place(456)
            print(place.title)
            ```
        """
        logger.debug(f"Fetching place with ID: {place_id}")
        try:
            place_response = await self._requests.get(
                url=self.url_generator.get_url(f"places/{place_id}", "api")
            )
        except NotFound as exception:
            raise PlaceNotFound(
                message="Invalid place.", response=exception.response
            ) from None

        place_data = place_response.json()
        logger.debug(f"Successfully retrieved place data for ID: {place_id}")
        return Place(client=self, data=place_data)

    async def get_group(self, group_id: int) -> Group:
        """
        Retrieve a group by its unique group ID.

        Args:
            group_id (int): The ID of the group to retrieve.

        Returns:
            Group: A Group object representing the requested group.

        Raises:
            GroupNotFound: If the group does not exist.

        Example:
            ```python
            group = await client.get_group(789)
            print(group.name)
            ```
        """
        logger.debug("Fetching group with ID: %s", group_id)
        try:
            group_response = await self.requests.get(
                url=self.url_generator.get_url(f"groups/{group_id}")
            )
        except NotFound as exception:
            raise GroupNotFound(
                message="Invalid group.", response=exception.response
            ) from None

        group_data = group_response.json()
        logger.debug(f"Successfully retrieved group data for ID: {group_id}")
        return Group(client=self, data=group_data)

    async def close(self):
        """
        Close the underlying HTTP session used by the client.
        """
        await self._requests.session.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
