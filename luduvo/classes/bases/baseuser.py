"""

This module contains the BaseUser object, which represents a Luduvo user ID.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .baseitem import BaseItem
from ...utilities.iterators import AsyncPaginator

if TYPE_CHECKING:
    from ...client import Client
    from ..friends import Friend


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

        async def fetch_page(offset: int):
            response = await self.client._requests.get(
                url=self.client.url_generator.get_url(
                    f"users/{self.id}/friends", "api"
                ),
                params={"limit": page_size, "offset": offset},
            )

            response.raise_for_status()
            data = response.json()

            return {
                "items": [
                    Friend(client=self.client, data=f) for f in data.get("friends", [])
                ],
                "total": data.get("total", 0),
            }

        return AsyncPaginator(fetch_page)

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
