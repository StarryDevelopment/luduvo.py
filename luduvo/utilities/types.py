from enum import Enum


class GroupAccess(Enum):
    """Represents the access type of a Luduvo group."""

    PUBLIC = "public"
    INVITE_ONLY = "invite_only"


class PlaceAccess(Enum):
    """Represents the access type of a Luduvo place."""

    PUBLIC = "public"
    PRIVATE = "private"
