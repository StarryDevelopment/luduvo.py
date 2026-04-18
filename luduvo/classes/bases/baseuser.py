"""

This module contains the BaseUser object, which represents a Luduvo user ID.

"""

from __future__ import annotations

from .baseitem import BaseItem


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

    async def get_friends(self, limit: int = 50) -> list["Friend"]:
        from ..friends import Friend

        """Gets the user's friends.

        Args:
            limit (int, optional): The maximum number of friends to retrieve. Defaults to 50.

        Returns:
            list[Friend]: A list of the user's friends.
        """
        offset = 0
        friends: list["Friend"] = []

        while True:
            response = await self.client._requests.get(
                url=self.client.url_generator.get_url(
                    f"users/{self.id}/friends", "api"
                ),
                params={"limit": limit, "offset": offset},
            )

            data = response.json()

            page_friends = [Friend(client=self.client, data=f) for f in data["friends"]]

            friends.extend(page_friends)

            offset += limit

            if offset >= data["total"] or not page_friends:
                break

        return friends
