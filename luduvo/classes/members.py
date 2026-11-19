"""
This module contains classes intended to parse and deal with data from Luduvo group member endpoints.

"""

from typing import Union, TYPE_CHECKING
import datetime

from .bases import BaseUser
from .group_roles import GroupRole
from .bases.basegroup import BaseGroup

if TYPE_CHECKING:
    from ..client import Client


class MemberRelationship(BaseUser):
    """
    Represents a relationship between a user and a group.

    Attributes:
        group: The corresponding group.
    """

    def __init__(
        self,
        client: "Client",
        user: Union[BaseUser, int],
        group: Union["BaseGroup", int],
    ):
        self._client: Client = client
        super().__init__(client=self._client, user_id=int(user))

        self.group: BaseGroup

        if isinstance(group, int):
            self.group = BaseGroup(client=self._client, group_id=group)
        else:
            self.group = group


class Member(MemberRelationship):
    """
    Represents a group member.

    Attributes:
        id: The member's ID.
        username: The member's username.
        joined_at: The datetime the member joined group.
    """

    def __init__(self, client: "Client", data: dict, group: "BaseGroup"):
        self._client: Client = client
        self.id: int = data["user_id"]
        self.username: str = data["username"]
        self.joined_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["joined_at"]
        )

        super().__init__(client=self._client, user=self.id, group=group)

        self.group: BaseGroup = group
        self.roles = [GroupRole.from_api(role) for role in data.get("roles") or []]
        self.permissions: int | None = data.get("permissions")
        self.headshot_url = data.get("headshot_url")
        self.status = data.get("status")
        self.banned = data.get("banned")

    def has_role(self, role_id: int) -> bool:
        """Check the roles in this membership snapshot."""
        return any(role.id == role_id for role in self.roles)

    async def add_role(self, role_id: int) -> bool:
        """Assign a role; fetch the member again to refresh its snapshot."""
        return await self.group.add_member_role(self.id, role_id)

    async def remove_role(self, role_id: int) -> bool:
        """Remove a role; fetch the member again to refresh its snapshot."""
        return await self.group.remove_member_role(self.id, role_id)

    @classmethod
    def from_api(cls, client: "Client", data: dict, group: "BaseGroup") -> "Member":
        """
        Create a Member instance from raw API response data.

        Args:
            client: The client instance used to interact with the API.
            data (dict): Raw member data returned by the API.
            group: The group to which this member belongs.

        Returns:
            Member: A fully constructed Member object.
        """
        return cls(client=client, data=data, group=group)

    async def kick(self) -> bool:
        """
        Remove the member from the group.

        Sends a request to the API to kick the member from their associated group.

        Returns:
            bool: True if the operation was successful.

        Raises:
            UserNotMemberOfGroup: If the user is not currently a member of the group.

        Example:
            ```python
            await member.kick()
            ```
        """

        return await self.group.kick_member(self.id)


    async def ban(self, reason: str | None = None) -> bool:
        """
        Ban a member from the group.

        This method removes the member from the group and prevents them from rejoining.
        A ban reason can optionally be provided and will be sent to the API.

        Args:
            reason (str | None, optional): The reason for banning the user. Defaults to None.

        Returns:
            bool: True if the operation was successfully completed.

        Raises:
            UserNotMemberOfGroup: If the user is not currently a member of the group.

        Example:
            ```python
            await member.ban(reason="Violation of rules")
            ```
        """

        return await self.group.ban_member(self.id, reason=reason)


    async def unban(self) -> bool:
        """
        Unban a member from the group.

        This method restores a previously banned member, allowing them to rejoin the group.

        Returns:
            bool: True if the unban operation was successful, otherwise False.

        Raises:
            MemberNotBanned: If the member is not currently banned.

        Example:
            ```python
            await member.unban()
            ```
        """

        return await self.group.unban_member(self.id)

