"""
This module contains the BasePlace object, which represents a Luduvo place ID.

"""

from __future__ import annotations

from .baseitem import BaseItem
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import Client


class BasePlace(BaseItem):
    """
    Represents a Luduvo place ID.

    Attributes:
        id: The place ID.
    """

    def __init__(self, client: "Client", place_id: int):
        """
        Arguments:
            client: The Client this object belongs to.
            place_id: The place ID.
        """

        self._client = client
        self.id: int = place_id
