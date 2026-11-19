"""

This module contains the BaseUser object, which represents a Luduvo user ID.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .baseitem import BaseItem
from ...utilities.iterators import AsyncPaginator
from ..presence import Presence
from ...utilities.resources import paginate
from ...models import JSONObject

if TYPE_CHECKING:
    from ...client import Client
    from ..friends import Friend
    from ..groups import Group


class BaseUser(BaseItem):
    """
    Represents a Luduvo user ID.

    Attributes:
        id: The user ID.
    """

    def __init__(self, client: "Client", user_id: int):
        """
        Arguments:
            client: The Client this object belongs to.
            user_id: The user ID.
        """

        self.client = client
        self.id: int = user_id

    async def get_presence(self) -> Presence:
        response = await self.client.requests.get(
            self.client.url_generator.get_url(f"users/{self.id}/presence")
        )
        return Presence.from_api(response.json(), self.id)

    def groups(self, page_size: int = 50) -> AsyncPaginator[Group]:
        """Iterate the groups this user belongs to."""
        return self.client._groups(f"users/{self.id}/groups", page_size)

    def usernames(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self.client, f"users/{self.id}/usernames", "items", page_size)

    def places(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self.client, f"users/{self.id}/places", "places", page_size)

    def inventory(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return paginate(self.client, f"users/{self.id}/inventory", "items", page_size)

    async def get_full_body_url(self) -> str | None:
        response = await self.client.requests.get(
            self.client.url_generator.get_url(f"users/{self.id}/avatar/full-body"),
            follow_redirects=False,
        )
        return response.headers.get("Location")

    def friends(self, page_size: int = 50) -> AsyncPaginator["Friend"]:
        """Returns an async paginator over the user's friends.

        This provides a lazy, memory-efficient way to iterate through all
        friends. Friends are fetched in pages from the API and yielded as
        `Friend` objects.

        Args:
            page_size (int, optional): Number of friends returned per API request.
                Controls pagination size. Defaults to 50.

        Returns:
            AsyncPaginator[Friend]: Async iterator yielding `Friend` objects.

        Example:
            Iterating asynchronously:
                ```python
                async for friend in user.friends():
                    print(friend.username)
                ```

            Or collecting all friends at once:
                ```python
                friends = await user.friends().flatten()
                ```
        """

        from ..friends import Friend

        return paginate(self.client, f"users/{self.id}/friends", "friends",
                        page_size, transform=lambda data: Friend(client=self.client, data=data))

    async def get_headshot_url(self) -> str | None:
        """Gets the user's headshot url.

        Returns:
            str: Headshot URL
        """
        try:
            response = await self.client.requests.get(
                url=self.client.url_generator.get_url(
                    f"users/{self.id}/avatar/headshot"
                ),
                follow_redirects=False,
            )
            url = response.headers.get("Location", None)
            return url
        except Exception:
            return None

    iter_groups = groups
    iter_usernames = usernames
    iter_places = places
    iter_inventory = inventory
    iter_friends = friends
