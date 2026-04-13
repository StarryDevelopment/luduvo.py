"""
This module contains classes intended to parse and deal with data from Luduvo place information endpoints.
"""

from .bases.baseplace import BasePlace
import datetime
from typing import TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..client import Client


class PlaceAccess(Enum):
    """Represents the access type of a Luduvo place."""

    PUBLIC = "public"
    PRIVATE = "private"


class Place(BasePlace):
    """
    Represents a Luduvo place.

    Attributes:
        id: The place ID.
        owner_id: The user ID of the place's owner.
        owner_username: The username of the place's owner.
        title: The place's title.
        description: The place's description.
        access: The place's access type.
        max_players: The maximum number of players allowed in the place.
        visit_count: The number of times the place has been visited.
        thumbs_up: The number of thumbs up the place has.
        thumbs_down: The number of thumbs down the place has.
        active_players: The number of active players in the place.
        created_at: The date and time the place was created.
        updated_at: The date and time the place was last updated.
        thumbnail_url: The URL of the place's thumbnail.
        has_map: Unknown
        tags: A list of tags associated with the place.
    """

    def __init__(self, client: Client, data: dict):
        """
        Arguments:
            client: The Client this object belongs to.
            data: The place data to parse.
        """
        super().__init__(client, data["id"])

        self.owner_id: int = data["owner_id"]
        self.owner_username: str = data["owner_username"]
        self.title: str = data["title"]
        self.description: str = data["description"]
        self.access: PlaceAccess = PlaceAccess(data["access"])
        self.max_players: int = data["max_players"]
        self.visit_count: int = data["visit_count"]
        self.thumbs_up: int = data["thumbs_up"]
        self.thumbs_down: int = data["thumbs_down"]
        self.active_players: int = data["active_players"]
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["created_at"]
        )
        self.updated_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["updated_at"]
        )
        self.thumbnail_url: str = data["thumbnail_url"]
        self.has_map: bool = data["has_map"]
        self.tags: list[str] = data["tags"]
