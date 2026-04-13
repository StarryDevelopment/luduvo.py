"""

This file contains partial objects related to Luduvo users.

"""

import datetime
from ..bases.baseuser import BaseUser


class PartialUser(BaseUser):
    """
    Represents a partial Luduvo user, containing only basic information.

    Attributes:
        id: The user's ID.
        username: The user's username.
        display_name: The user's display name.
        created_at: The datetime the user joined Luduvo.
    """

    def __init__(self, client, data):
        super().__init__(client, data.get("user_id") or data.get("id"))
        self.username: str = data.get("username")
        self.display_name: str = data.get("display_name")
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data.get("created_at")
        )
        self._client = client

    def __repr__(self):
        return f"<PartialUser id={self.id} username={self.username}>"
