import unittest
from unittest.mock import AsyncMock, Mock
import httpx
from luduvo.classes.members import Member
from luduvo.classes.bases.basegroup import BaseGroup
from luduvo.utilities.exceptions import BadRequest


class ModerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_member_delegates(self):
        member = object.__new__(Member)
        member.id = 42
        member.group = Mock()
        for name in ("kick_member", "ban_member", "unban_member"):
            setattr(member.group, name, AsyncMock(return_value=True))
        self.assertTrue(await member.kick())
        self.assertTrue(await member.ban("test"))
        self.assertTrue(await member.unban())
        member.group.kick_member.assert_awaited_once_with(42)
        member.group.ban_member.assert_awaited_once_with(42, reason="test")
        member.group.unban_member.assert_awaited_once_with(42)

    async def test_ban_json_and_error_propagation(self):
        client = Mock()
        client.url_generator.get_url.return_value = (
            "https://api.luduvo.com/groups/1/ban/42"
        )
        client.requests.post = AsyncMock(return_value=httpx.Response(204))
        group = BaseGroup(client, 1)
        self.assertTrue(await group.ban_member(42, "test"))
        client.requests.post.assert_awaited_once_with(
            url="https://api.luduvo.com/groups/1/ban/42", json={"reason": "test"}
        )
        client.requests.post.side_effect = BadRequest(response=httpx.Response(400))
        with self.assertRaises(BadRequest):
            await group.ban_member(42)
