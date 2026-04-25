"""

This module contains classes intended to parse and deal with data from Luduvo user information endpoints.

"""

from __future__ import annotations

import datetime
from .bases.baseuser import BaseUser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


class User(BaseUser):
    """
    Represents a Luduvo user.

    Attributes:
        id: The user's ID.
        username: The user's username.
        created_at: The datetime the user joined Luduvo.
        display_name: The user's display name.
        status: The user's status message.
        bio: The user's biography.
        avatar: A dictionary containing information about the user's avatar.
        accent_color: The user's accent color.
        banner_url: The URL of the user's banner image.
        equipped_items: A list of items currently equipped by the user.
        badges: A list of badges owned by the user.
        friend_count: The number of friends the user has.
        place_count: The number of places owned by the user.
        item_count: The number of items owned by the user.
        last_active:
        allow_joins: Whether the user allows others to join their games.
    """

    def __init__(self, client: "Client", data: dict):
        """
        Arguments:
            client: The Client this object belongs to.
            data: The data we got from endpoint.
        """
        super().__init__(client, data["user_id"])
        self.username: str = data["username"]
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["member_since"]
        )
        self.display_name: str = data["display_name"]
        self.status: str = data["status"]
        self.bio: str = data["bio"]
        self.avatar: dict = data["avatar"]
        self.accent_color: str = data["accent_color"]
        self.banner_url: str = data["banner_url"]
        self.equipped_items: list = data["equipped_items"]
        self.badges: list = data["badges"]
        self.friend_count: int = data["friend_count"]
        self.place_count: int = data["place_count"]
        self.item_count: int = data["item_count"]
        self.last_active = data["last_active"]
        self.allow_joins: bool = data["allow_joins"]
        self.__client__ = client

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"
