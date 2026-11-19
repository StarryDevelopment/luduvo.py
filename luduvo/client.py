"""Contains the main client class for interacting with the Luduvo API."""

import logging
from collections.abc import Iterable
from .models import JSONObject, JSONValue, TradeKind
from .utilities.resources import paginate, get_json
from .classes.search import UserSearchResult
from .classes.friends import Friend
from .classes import User, Place, Group, BaseGroup, BaseUser, Presence
from .utilities.iterators import AsyncPaginator
from .utilities.exceptions import NotFound, UserNotFound, PlaceNotFound, GroupNotFound
from .utilities.url import URLGenerator
from .utilities.requests import Requests
from .session import SessionTokens, TokenRefreshCallback


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

    def __init__(self, *, base_url: str = "luduvo.com", token: str | None = None,
                 refresh_token: str | None = None, timeout: float = 15.0,
                 max_concurrency: int = 4, max_retries: int = 2,
                 max_retry_after: float = 60.0, refresh_margin: float = 60.0,
                 on_token_refresh: TokenRefreshCallback | None = None) -> None:
        """
        Initialize a Luduvo Client instance.

        Args:
            token (str, optional): Access token from an authorized session.
            refresh_token (str, optional): Refresh token for that session.
            base_url (str, optional): Base URL for the Luduvo API.
            refresh_margin: Seconds before JWT expiration to refresh on demand.
            on_token_refresh: Async callback to persist rotated credentials.

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
                                  max_retry_after=max_retry_after, refresh_margin=refresh_margin,
                                  on_token_refresh=on_token_refresh)
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

    def __repr__(self) -> str:
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

    def _groups(self, path: str, page_size: int, **params: str | int) -> AsyncPaginator[Group]:
        return paginate(self, path, "groups", page_size,
                        transform=lambda data: Group(self, data), **params)

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

    def search_users(self, query: str, page_size: int = 50) -> AsyncPaginator[UserSearchResult]:
        return paginate(self, "users", "users", page_size, q=query,
                        transform=lambda data: UserSearchResult(self, data))

    def search_places(self, query: str, page_size: int = 50, *, sort: str | None = None) -> AsyncPaginator[JSONObject]:
        params = {"q": query}
        if sort is not None:
            params["sort"] = sort
        return paginate(self, "places", "places", page_size, **params)

    def search_store(self, page_size: int = 50, *, sort: str | None = None, made_by: str | int | None = None) -> AsyncPaginator[JSONObject]:
        params = {k: v for k, v in {"sort": sort, "made_by": made_by}.items()
                  if v is not None}
        return paginate(self, "store", "items", page_size, **params)

    async def get_store_item(self, item_id: int) -> JSONObject:
        return await get_json(self, f"store/{item_id}")

    async def get_item_variants(self, item_id: int) -> list[JSONValue]:
        return (await get_json(self, f"items/{item_id}/variants"))["variants"]

    async def get_store_categories(self) -> list[JSONValue]:
        return await get_json(self, "store/categories")

    def my_inventory(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self, "me/inventory", "items", page_size)

    def my_friends(self, page_size: int = 50) -> AsyncPaginator[Friend]:
        return paginate(self, "me/friends", "friends", page_size,
                        transform=lambda data: Friend(client=self, data=data))

    def pending_friends(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self, "me/friends/pending", "requests", page_size)

    def my_ignores(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self, "me/ignores", "items", page_size)

    async def my_balance(self) -> int:
        return (await get_json(self, "me/balance"))["balance"]

    async def my_outfits(self) -> list[JSONValue]:
        return (await get_json(self, "me/outfits"))["outfits"]

    def recently_played(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self, "me/recently-played", "places", page_size)

    def conversations(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self, "me/conversations", "conversations", page_size)

    async def conversation_messages(self, conversation_id: int, *, limit: int = 50) -> JSONObject:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return await get_json(self, f"conversations/{conversation_id}/messages", limit=limit)

    async def trade_counts(self) -> JSONObject:
        return await get_json(self, "me/trades/counts")

    def trades(self, kind: TradeKind, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        if kind not in {"received", "sent", "history"}:
            raise ValueError("Unknown trade kind")
        return paginate(self, f"me/trades/{kind}", "trades", page_size)

    async def site_banners(self) -> list[JSONValue]:
        return (await get_json(self, "site/banners"))["items"]

    async def site_promos(self) -> list[JSONValue]:
        return (await get_json(self, "site/promos"))["items"]

    async def get_presences(self, user_ids: Iterable[int], *, batch_size: int = 50) -> list[Presence]:
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

    async def discover_places(self, *, surface: str = "discover", limit: int = 20) -> JSONObject:
        return await get_json(self, "places/discovery", surface=surface, limit=limit)

    async def featured_events(self) -> list[JSONValue]:
        return (await get_json(self, "featured/events"))["items"]

    async def official_messages(self, *, limit: int = 50) -> JSONObject:
        return await get_json(self, "me/official-messages", limit=limit)

    async def get_subscription(self) -> JSONObject:
        return await get_json(self, "me/subscription")

    async def pending_payments(self) -> list[JSONValue]:
        return (await get_json(self, "me/pending-payments"))["pending"]

    async def close(self) -> None:
        """
        Close the underlying HTTP session used by the client.
        """
        await self._requests.close()

    async def __aenter__(self) -> "Client":
        try:
            await self.requests.ensure_authenticated()
        except BaseException:
            await self.close()
            raise
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # Consistent public aliases; legacy names remain supported.
    get_me = get_authenticated_user
    iter_my_groups = get_my_groups
    iter_my_inventory = my_inventory
    iter_my_friends = my_friends
    iter_pending_friends = pending_friends
    iter_my_ignores = my_ignores
    get_my_balance = my_balance
    get_my_outfits = my_outfits
    iter_recently_played = recently_played
    iter_conversations = conversations
    get_conversation_messages = conversation_messages
    get_trade_counts = trade_counts
    iter_trades = trades
    get_site_banners = site_banners
    get_site_promos = site_promos
    get_featured_events = featured_events
    get_official_messages = official_messages
    get_pending_payments = pending_payments
