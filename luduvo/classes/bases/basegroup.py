"""
This module contains the BaseGroup object, which represents a Luduvo group ID.
"""

from __future__ import annotations
from luduvo.utilities.exceptions import UserNotMemberOfGroup, NotFound, MemberNotBanned

from .baseitem import BaseItem
from ...utilities.iterators import AsyncPaginator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import Client
    from ..members import Member


class BaseGroup(BaseItem):
    """
    Represents a Luduvo group.

    This class provides core functionality for interacting with a group,
    including accessing its members and retrieving individual member data.

    Attributes:
        id (int): The unique identifier of the group.
    """

    def __init__(self, client: "Client", group_id: int):
        """
        Initialize a BaseGroup instance.

        Args:
            client (Client): The client instance associated with this group.
            group_id (int): The unique identifier of the group.
        """

        self._client = client
        self.id: int = group_id

    def members(self, page_size: int = 50) -> AsyncPaginator["Member"]:
        """
        Return an asynchronous paginator over the group's members.

        This method provides a memory-efficient way to iterate through all
        members in the group. Members are retrieved in pages from the API
        and yielded as `Member` objects.

        Args:
            page_size (int, optional): Number of members retrieved per API
                request. Used for pagination control. Defaults to 50.

        Returns:
            AsyncPaginator[Member]: An asynchronous iterator yielding `Member` objects.

        Example:
            Iterating asynchronously:
                ```python
                async for member in group.members():
                    print(member.username)
                ```

            Or collecting all members at once:
                ```python
                members = await group.members().flatten()
                ```
        """

        from ..members import Member

        async def fetch_page(offset: int):
            response = await self._client.requests.get(
                url=self._client.url_generator.get_url(
                    f"groups/{self.id}/members", "api"
                ),
                params={"limit": page_size, "offset": offset},
            )

            response.raise_for_status()
            data = response.json()

            return {
                "items": [
                    Member.from_api(self._client, m, self)
                    for m in data.get("members", [])
                ],
                "total": data.get("total", 0),
            }

        return AsyncPaginator(fetch_page)

    async def get_member(self, user_id: int) -> Member:
        """
        Retrieve a single group member by user ID.

        This method searches through the group's members using the paginated
        members endpoint until a matching user ID is found.

        Note:
            This operation may require multiple API requests depending on the
            position of the user in the member list.

        Args:
            user_id (int): The unique identifier of the member to retrieve.

        Returns:
            Member: The matching `Member` object.

        Raises:
            UserNotMemberOfGroup: If the specified user is not found in the group.

        Example:
            ```python
            member = await group.get_member(123)
            print(member.username)
            ```
        """

        async for member in self.members():
            if member.id == user_id:
                return member

        raise UserNotMemberOfGroup(message="User not member of group.")

    async def kick_member(self, user_id: int) -> bool:
        """
        Remove the member from the group.

        Sends a request to the API to kick the member from the group.

        Args:
            user_id (int): The Luduvo user ID of the member to kick.

        Returns:
            bool: True if the operation was successful.

        Raises:
            UserNotMemberOfGroup: If the user is not currently a member of the group.

        Example:
            ```python
            await group.kick_member(123)
            ```
        """

        try:
            response = await self._client.requests.post(
                url=self._client.url_generator.get_url(
                    f"groups/{self.id}/kick/{user_id}"
                )
            )
            if response.status_code == 204:
                return True
            else:
                return False
        except NotFound as exception:
            raise UserNotMemberOfGroup(
                message="User not member of group.", response=exception.response
            ) from None

    async def ban_member(self, user_id: int, reason: str | None = None) -> bool:
        """
        Ban a user from the group.

        This method removes the specified user from the group and prevents them
        from rejoining. An optional reason can be provided and will be forwarded
        to the API.

        Args:
            user_id (int): The Luduvo user ID of the member to ban.
            reason (str | None, optional): The reason for banning the user.
                Defaults to None.

        Returns:
            bool: True if the ban operation was successful, otherwise False.

        Example:
            ```python
            await group.ban_member(123, reason="Violation of rules")
            ```
        """

        try:
            response = await self._client.requests.post(
                url=self._client.url_generator.get_url(
                    f"groups/{self.id}/ban/{user_id}"
                ),
                json={"reason": reason},
            )
            if response.status_code == 204:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    async def unban_member(self, user_id: int) -> bool:
        """
        Unban a member from the group.

        This method restores a previously banned member, allowing them to rejoin the group.

        Returns:
            bool: True if the unban operation was successful, otherwise False.

        Raises:
            MemberNotBanned: If the member is not currently banned.

        Example:
            ```python
            await group.unban_member(123)
            ```
        """

        try:
            response = await self._client.requests.delete(
                url=self._client.url_generator.get_url(
                    f"groups/{self.id}/bans/{user_id}"
                )
            )
            if response.status_code == 204:
                return True
            else:
                return False
        except NotFound as exception:
            raise MemberNotBanned(
                message="Member not banned.", response=exception.response
            ) from None
