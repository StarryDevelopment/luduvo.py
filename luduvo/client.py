"""Contains the main client class for interacting with the Luduvo API."""

import logging
from .utilities.resources import paginate, get_json
from .classes.search import UserSearchResult
from .classes.friends import Friend
from .classes import User, Place, Group, BaseGroup, BaseUser, Presence
from .utilities.iterators import AsyncPaginator
from .utilities.exceptions import NotFound, UserNotFound, PlaceNotFound, GroupNotFound
from .utilities.url import URLGenerator
from .utilities.requests import Requests
from .session import SessionTokens


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

    def __init__(self, *, base_url="luduvo.com", token=None, refresh_token=None,
                 timeout=15.0, max_concurrency=4, max_retries=2, max_retry_after=60.0):
        """
        Initialize a Luduvo Client instance.

        Args:
            token (str, optional): Access token from an authorized session.
            refresh_token (str, optional): Refresh token for that session.
            base_url (str, optional): Base URL for the Luduvo API.

        Example:
            ```python
            client = Client(token=access_token, refresh_token=refresh_token)
            ```
        """
        logger.debug("Initializing Client(base_url=%s)", base_url)

        self._url_generator: URLGenerator = URLGenerator(base_url=base_url)

        self._requests = Requests(base_url=base_url, token=token, refresh_token=refresh_token,
                                  timeout=timeout,
                                  max_concurrency=max_concurrency, max_retries=max_retries,
                                  max_retry_after=max_retry_after)
        self.url_generator = self._url_generator
        self.requests = self._requests

    @property
    def authenticated(self) -> bool:
        return self.requests.authenticated

    @property
    def tokens(self) -> SessionTokens | None:
        """Current credentials, including any rotated refresh token."""
        return self.requests.tokens

    async def refresh(self) -> SessionTokens:
        return await self.requests.refresh()

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
        await self.requests.ensure_authenticated()
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

    def _groups(self, path: str, page_size: int, **params) -> AsyncPaginator[Group]:
        if page_size <= 0:
            raise ValueError("page_size must be positive")

        async def fetch_page(offset: int):
            response = await self.requests.get(
                self.url_generator.get_url(path),
                params={**params, "limit": page_size, "offset": offset},
            )
            data = response.json()
            return {"items": [Group(self, item) for item in data["groups"]],
                    "total": data["total"]}

        return AsyncPaginator(fetch_page)

    def search_groups(self, query: str, page_size: int = 50) -> AsyncPaginator[Group]:
        return self._groups("groups", page_size, q=query)

    def get_my_groups(self, page_size: int = 50) -> AsyncPaginator[Group]:
        return self._groups("me/groups", page_size)

    def get_partial_group(self, group_id: int) -> BaseGroup:
        return BaseGroup(self, group_id)

    def get_partial_user(self, user_id: int) -> BaseUser:
        return BaseUser(self, user_id)

    async def get_presence(self, user_id: int) -> Presence:
        return await self.get_partial_user(user_id).get_presence()

    def search_users(self, query: str, page_size: int = 50):
        return paginate(self, "users", "users", page_size, q=query,
                        transform=lambda data: UserSearchResult(self, data))

    def search_places(self, query: str, page_size: int = 50, *, sort=None):
        params = {"q": query}
        if sort is not None:
            params["sort"] = sort
        return paginate(self, "places", "places", page_size, **params)

    def search_store(self, page_size: int = 50, *, sort=None, made_by=None):
        params = {k: v for k, v in {"sort": sort, "made_by": made_by}.items()
                  if v is not None}
        return paginate(self, "store", "items", page_size, **params)

    async def get_store_item(self, item_id: int):
        return await get_json(self, f"store/{item_id}")

    async def get_item_variants(self, item_id: int):
        return (await get_json(self, f"items/{item_id}/variants"))["variants"]

    async def get_store_categories(self):
        return await get_json(self, "store/categories")

    def my_inventory(self, page_size: int = 50):
        return paginate(self, "me/inventory", "items", page_size)

    def my_friends(self, page_size: int = 50):
        return paginate(self, "me/friends", "friends", page_size,
                        transform=lambda data: Friend(client=self, data=data))

    def pending_friends(self, page_size: int = 50):
        return paginate(self, "me/friends/pending", "requests", page_size)

    def my_ignores(self, page_size: int = 50):
        return paginate(self, "me/ignores", "items", page_size)

    async def my_balance(self) -> int:
        return (await get_json(self, "me/balance"))["balance"]

    async def my_outfits(self):
        return (await get_json(self, "me/outfits"))["outfits"]

    def recently_played(self, page_size: int = 50):
        return paginate(self, "me/recently-played", "places", page_size)

    def conversations(self, page_size: int = 50):
        return paginate(self, "me/conversations", "conversations", page_size)

    async def conversation_messages(self, conversation_id: int, *, limit: int = 50):
        if limit <= 0:
            raise ValueError("limit must be positive")
        return await get_json(self, f"conversations/{conversation_id}/messages", limit=limit)

    async def trade_counts(self):
        return await get_json(self, "me/trades/counts")

    def trades(self, kind: str, page_size: int = 50):
        if kind not in {"received", "sent", "history"}:
            raise ValueError("Unknown trade kind")
        return paginate(self, f"me/trades/{kind}", "trades", page_size)

    async def site_banners(self):
        return (await get_json(self, "site/banners"))["items"]

    async def site_promos(self):
        return (await get_json(self, "site/promos"))["items"]

    async def get_presences(self, user_ids, *, batch_size: int = 50) -> list[Presence]:
        """Fetch presence in batches; missing users are not treated as offline."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        ids = list(dict.fromkeys(int(user_id) for user_id in user_ids))
        result = []
        for offset in range(0, len(ids), batch_size):
            batch = ids[offset:offset + batch_size]
            data = await get_json(self, "users/presence",
                                  ids=",".join(map(str, batch)))
            result.extend(Presence.from_api(item) for item in data["presence"])
        return result

    async def discover_places(self, *, surface: str = "discover", limit: int = 20):
        return await get_json(self, "places/discovery", surface=surface, limit=limit)

    async def featured_events(self):
        return (await get_json(self, "featured/events"))["items"]

    async def official_messages(self, *, limit: int = 50):
        return await get_json(self, "me/official-messages", limit=limit)

    async def get_subscription(self):
        return await get_json(self, "me/subscription")

    async def pending_payments(self):
        return (await get_json(self, "me/pending-payments"))["pending"]

    async def close(self):
        """
        Close the underlying HTTP session used by the client.
        """
        await self._requests.close()

    async def __aenter__(self):
        try:
            await self.requests.ensure_authenticated()
        except BaseException:
            await self.close()
            raise
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
