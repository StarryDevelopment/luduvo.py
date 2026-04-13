"""

Contains classes related to Luduvo friend data and parsing.

"""

from .bases.baseuser import BaseUser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


class Friend(BaseUser):
    """
    Represents a friend of a Luduvo user.

    Attributes:
        id: The friend's user ID.
        username: The friend's username.
    """

    def __init__(self, client: "Client", data: dict):
        """
        Arguments:
            client: The Client this object belongs to.
            data: The data we got from endpoint.
        """
        super().__init__(client, data["user_id"])
        self.username: str = data["username"]
        self.client = client

    def __repr__(self):
        return f"<Friend id={self.id} username={self.username}>"
