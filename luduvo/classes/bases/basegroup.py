"""
This module contains the BaseGroup object, which represents a Luduvo group ID.

"""

from __future__ import annotations

from .baseitem import BaseItem
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import Client
    from ..members import Member


class BaseGroup(BaseItem):
    """
    Represents a Luduvo group ID.

    Attributes:
        id: The group ID.
    """

    def __init__(self, client: "Client", group_id: int):
        """
        Arguments:
            client: The Client this object belongs to.
            group_id: The group ID.
        """

        self._client = client
        self.id: int = group_id

    async def get_members(self, limit: int = 50) -> list["Member"]:
        from ..members import Member

        """Gets the group's members.

        Args:
            limit (int, optional): The maximum number of members to retrieve. Defaults to 50.

        Returns:
            list[Member]: A list of the group's members.
        """
        offset = 0
        members: list["Member"] = []

        while True:
            response = await self._client.requests.get(
                url=self._client.url_generator.get_url(
                    f"groups/{self.id}/members", "api"
                ),
                params={"limit": limit, "offset": offset},
            )

            data = response.json()

            page_members = [
                Member(client=self._client, data=f, group=self) for f in data["members"]
            ]

            members.extend(page_members)

            offset += limit

            if offset >= data["total"] or not page_members:
                break

        return members
