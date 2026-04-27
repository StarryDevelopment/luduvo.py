"""

This module contains classes intended to parse and deal with data from Luduvo group member endpoints.

"""

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
