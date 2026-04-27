"""
This module contains classes intended to parse and deal with data from Luduvo group information endpoints.
"""

from __future__ import annotations

from .bases.basegroup import BaseGroup
import datetime
from typing import TYPE_CHECKING

from ..utilities.types import GroupAccess

if TYPE_CHECKING:
    from ..client import Client


class Group(BaseGroup):
    """
    Represents a Luduvo group.

    Attributes:
        id: The group ID.
        name: The group name.
        description: The group description.
        owner_id: The user ID of the group's owner.
        owner_username: The username of the group's owner.
        access: The group access type.
        member_count: The group member count.
        icon_url: The group icon URL.
        created_at: When group was created.
        updated_at: When group was updated.
    """

    def __init__(self, client: "Client", data: dict):
        """
        Arguments:
            client: The Client this object belongs to.
            data: The place data to parse.
        """
        super().__init__(client, data["id"])

        self.name: str = data["name"]
        self.description: str = data["description"]
        self.owner_id: int = data["owner_id"]
        self.owner_username: str = data["owner_username"]
        self.access: GroupAccess = GroupAccess(data["access"])
        self.member_count: int = data["member_count"]
        self.icon_url: int = data["icon_url"]
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["created_at"]
        )
        self.updated_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["updated_at"]
        )
