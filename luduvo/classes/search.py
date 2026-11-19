"""Lightweight user search results."""

from .bases.baseuser import BaseUser


class UserSearchResult(BaseUser):
    def __init__(self, client, data):
        super().__init__(client, data["id"])
        self.username = data["username"]
        self.display_name = data.get("display_name")
        self.headshot_url = data.get("headshot_url")
        self.role = data.get("role")
        self.created_at = data.get("created_at")

    async def fetch(self):
        return await self.client.get_user(self.id)
