"""

This file contains partial objects related to Luduvo users.

"""

from __future__ import annotations

import datetime
from ..bases.baseuser import BaseUser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import Client


class PartialUser(BaseUser):
    """
    Represents a partial Luduvo user, containing only basic information.

    Attributes:
        id: The user's ID.
        username: The user's username.
        display_name: The user's display name.
        created_at: The datetime the user joined Luduvo.
    """

    def __init__(self, client: "Client", data: dict):
        """
        Arguments:
            client: The Client this object belongs to.
            data: The data we got from endpoint.
        """

        super().__init__(client, data["user_id"])
        self.username: str = data["username"]
        self.display_name: str = data["display_name"]
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(
            data["created_at"]
        )
        self._client = client

    def __repr__(self):
        return f"<PartialUser id={self.id} username={self.username}>"
