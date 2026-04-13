"""

This module contains classes intended to parse and deal with data from Luduvo user information endpoints.

"""

import datetime
from .bases.baseuser import BaseUser


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
        equipped_items: A list of items currently equipped by the user.
        badges: A list of badges owned by the user.
        friend_count: The number of friends the user has.
        place_count: The number of places owned by the user.
        item_count: The number of items owned by the user.
        last_active:
        allow_joins: Whether the user allows others to join their games.
    """

    def __init__(self, client, data):
        super().__init__(client, data.get("user_id") or data.get("id"))
        self.username: str = data.get("username")
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data.get("member_since")
        )
        self.display_name: str = data.get("display_name")
        self.status: str = data.get("status")
        self.bio: str = data.get("bio")
        self.avatar: dict = data.get("avatar")
        self.equipped_items: list = data.get("equipped_items")
        self.badges: list = data.get("badges")
        self.friend_count: int = data.get("friend_count")
        self.place_count: int = data.get("place_count")
        self.item_count: int = data.get("item_count")
        self.last_active = data.get("last_active")
        self.allow_joins: bool = data.get("allow_joins")
        self.__client__ = client

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"
