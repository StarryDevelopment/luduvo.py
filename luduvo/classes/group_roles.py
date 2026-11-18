"""Luduvo group role metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GroupRole:
    """Role metadata; priority may be absent from membership responses."""

    id: int
    name: str
    permissions: int
    priority: int | None = None

    @classmethod
    def from_api(cls, data: dict) -> "GroupRole":
        return cls(data["id"], data["name"], data["permissions"], data.get("priority"))
