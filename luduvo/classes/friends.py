"""

Contains classes related to Luduvo friend data and parsing.

"""

from .bases.baseuser import BaseUser


class Friend(BaseUser):
    """
    Represents a friend of a Luduvo user.

    Attributes:
        id: The friend's user ID.
        username: The friend's username.
    """

    def __init__(self, _client, **data):
        super().__init__(_client, data["user_id"])
        self.username: str = data["username"]
        self._client = _client

    def __repr__(self):
        return f"<Friend id={self.id} username={self.username}>"
