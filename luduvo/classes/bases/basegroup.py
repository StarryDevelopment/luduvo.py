"""
This module contains the BaseGroup object, which represents a Luduvo group ID.
"""

from __future__ import annotations
from luduvo.utilities.exceptions import UserNotMemberOfGroup, NotFound, MemberNotBanned

from .baseitem import BaseItem
from ...utilities.iterators import AsyncPaginator
from ..group_roles import GroupRole
from ..group_metrics import GroupMetrics
from ...utilities.resources import paginate, get_json

from typing import TYPE_CHECKING
from ...models import JSONObject, JSONValue

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

    async def metrics(self, *, range: str) -> GroupMetrics:
        """Fetch analytics for an API-supported range using the current account."""
        response = await self._client.requests.get(
            self._client.url_generator.get_url(f"me/groups/{self.id}/metrics"),
            params={"range": range},
        )
        return GroupMetrics.from_api(response.json())

    def _paginate(
        self, resource: str, key: str, page_size: int
    ) -> AsyncPaginator[JSONObject]:
        return paginate(self._client, f"groups/{self.id}/{resource}", key, page_size)

    def bans(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        """Iterate raw ban records."""
        return self._paginate("bans", "bans", page_size)

    def announcements(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return self._paginate("announcements", "announcements", page_size)

    def wall_posts(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return self._paginate("wall", "posts", page_size)

    def places(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return self._paginate("places", "places", page_size)

    def store_items(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        return self._paginate("store", "items", page_size)

    def funds(self, page_size: int = 50) -> AsyncPaginator[JSONObject]:
        """Iterate group ledger entries (requires appropriate permissions)."""
        return paginate(self._client, f"groups/{self.id}/funds", "entries", page_size)

    async def get_funds_balance(self) -> int:
        data = await get_json(
            self._client, f"groups/{self.id}/funds", limit=1, offset=0
        )
        return data["balance_earned"]

    async def pending_transfer(self) -> JSONValue:
        return (await get_json(self._client, f"groups/{self.id}/transfer/pending"))[
            "pending"
        ]

    async def post_wall(
        self, content: str, *, announcement: bool = False
    ) -> JSONObject:
        """Publish a group wall post using the authenticated account."""
        if not content.strip():
            raise ValueError("content must not be empty")
        response = await self._client.requests.post(
            self._client.url_generator.get_url(f"groups/{self.id}/wall"),
            json={"content": content, "announcement": announcement},
        )
        return response.json()

    async def roles(self) -> list[GroupRole]:
        """Retrieve the group's available roles."""
        response = await self._client.requests.get(
            self._client.url_generator.get_url(f"groups/{self.id}/roles")
        )
        return [GroupRole.from_api(role) for role in response.json()]

    async def join(self) -> bool:
        """Join the group using the authenticated account."""
        response = await self._client.requests.post(
            self._client.url_generator.get_url(f"groups/{self.id}/join")
        )
        return response.status_code == 204

    async def leave(self) -> bool:
        """Leave the group using the authenticated account."""
        response = await self._client.requests.post(
            self._client.url_generator.get_url(f"groups/{self.id}/leave")
        )
        return response.status_code == 204

    async def add_member_role(self, user_id: int, role_id: int) -> bool:
        response = await self._client.requests.post(
            self._client.url_generator.get_url(
                f"groups/{self.id}/members/{user_id}/roles/{role_id}"
            )
        )
        return response.status_code == 204

    async def remove_member_role(self, user_id: int, role_id: int) -> bool:
        response = await self._client.requests.delete(
            self._client.url_generator.get_url(
                f"groups/{self.id}/members/{user_id}/roles/{role_id}"
            )
        )
        return response.status_code == 204

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

        return paginate(
            self._client,
            f"groups/{self.id}/members",
            "members",
            page_size,
            transform=lambda data: Member.from_api(self._client, data, self),
        )

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
        except NotFound as exception:
            raise UserNotMemberOfGroup(
                message="User not member of group.", response=exception.response
            ) from None

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

    get_metrics = metrics
    get_roles = roles
    get_pending_transfer = pending_transfer
    iter_members = members
    iter_bans = bans
    iter_announcements = announcements
    iter_wall_posts = wall_posts
    iter_places = places
    iter_store_items = store_items
    iter_funds = funds
