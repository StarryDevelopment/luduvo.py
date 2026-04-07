import datetime


class Friend:
    """
    Represents a friend of a Luduvo user.

    Attributes:
        id: The friend's user ID.
        username: The friend's username.
    """

    def __init__(self, __client__, **data):
        self.id: int = data["user_id"]
        self.username: str = data["username"]
        self.__client__ = __client__

    def __repr__(self):
        return f"<Friend id={self.id} username={self.username}>"


class User:
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
        self.id: int = data.get("user_id")
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

    async def get_friends(self, limit: int = 50) -> list[Friend]:
        """Gets the user's friends.

        Args:
            limit (int, optional): The maximum number of friends to retrieve. Defaults to 50.

        Returns:
            list[Friend]: A list of the user's friends.
        """
        offset = 0
        friends: list[Friend] = []

        while True:
            response = await self.__client__._requests.get(
                url=self.__client__.url_generator.get_url(
                    f"users/{self.id}/friends", "api"
                ),
                params={"limit": limit, "offset": offset},
            )

            data = response.json()

            page_friends = [
                Friend(__client__=self.__client__, **f) for f in data["friends"]
            ]

            friends.extend(page_friends)

            offset += limit

            if offset >= data["total"] or not page_friends:
                break

        return friends


class PartialUser:
    """
    Represents a partial Luduvo user, containing only basic information.

    Attributes:
        id: The user's ID.
        username: The user's username.
        display_name: The user's display name.
        created_at: The datetime the user joined Luduvo.
    """

    def __init__(self, client, data):
        self.id: int = data.get("id")
        self.username: str = data.get("username")
        self.display_name: str = data.get("display_name")
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data.get("created_at")
        )
        self.__client__ = client

    def __repr__(self):
        return f"<PartialUser id={self.id} username={self.username}>"
