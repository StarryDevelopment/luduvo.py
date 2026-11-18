"""User presence snapshots."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Presence:
    user_id: int
    state: str
    online: bool | None = None
    joinable: bool | None = None

    @classmethod
    def from_api(cls, data: dict, user_id: int | None = None) -> "Presence":
        return cls(data["user_id"] if user_id is None else user_id,
                   data["state"], data.get("online"), data.get("joinable"))
