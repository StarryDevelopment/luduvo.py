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
        self.display_name: str | None = data.get("display_name")
        self.status: str | None = data.get("status")
        self.bio: str = data.get("bio") or ""
        self.avatar: dict = data["avatar"]
        self.accent_color: str | None = data.get("accent_color")
        self.banner_url: str | None = data.get("banner_url")
        self.equipped_items: list = data["equipped_items"]
        self.badges: list = data["badges"]
        self.friend_count: int = data["friend_count"]
        self.place_count: int = data["place_count"]
        self.item_count: int = data["item_count"]
        self.last_active = data["last_active"]
        self.allow_joins: bool | None = data.get("allow_joins")
        self.join_policy = data.get("join_policy")
        self.headshot_url = data.get("headshot_url")
        self.visibility = data.get("visibility")
        self.networth = data.get("networth")
        self.tier = data.get("tier")
        self.is_owner = data.get("is_owner")
        self.background_url = data.get("background_url")
        self.wishlist_hidden = data.get("wishlist_hidden")
        self.inventory_hidden = data.get("inventory_hidden")
        self.friends_hidden = data.get("friends_hidden")
        self.friendship_status = data.get("friendship_status")
        self.viewer_ignores = data.get("viewer_ignores")
        self.can_message = data.get("can_message")
        self.mutual_count = data.get("mutual_count")
        self.mutuals = data.get("mutuals")
        self.__client__ = client

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"
