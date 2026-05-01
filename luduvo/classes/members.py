"""
This module contains classes intended to parse and deal with data from Luduvo group member endpoints.

"""

from luduvo.utilities.exceptions import NotFound, UserNotMemberOfGroup, MemberNotBanned

from typing import Union, TYPE_CHECKING
import datetime

from .bases import BaseUser

if TYPE_CHECKING:
    from ..client import Client
    from .bases.basegroup import BaseGroup


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

        try:
            response = await self.client.requests.post(
                url=self.client.url_generator.get_url(
                    f"groups/{self.group.id}/kick/{self.id}"
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

        try:
            response = await self.client.requests.post(
                url=self.client.url_generator.get_url(
                    f"groups/{self.group.id}/ban/{self.id}"
                ),
                data={"reason": reason},
            )
            if response.status_code == 204:
                return True
            else:
                return False
        except NotFound as exception:
            raise UserNotMemberOfGroup(
                message="User not member of group.", response=exception.response
            ) from None

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

        try:
            response = await self.client.requests.delete(
                url=self.client.url_generator.get_url(
                    f"groups/{self.group.id}/bans/{self.id}"
                )
            )
            if response.status_code == 204:
                return True
            else:
                return False
        except NotFound as exception:
            raise MemberNotBanned(
                message="Member is not banned.", response=exception.response
            ) from None
