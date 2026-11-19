import unittest
from unittest.mock import AsyncMock

import httpx
import luduvo
from luduvo.utilities.requests import Requests


class ReleaseContractTests(unittest.IsolatedAsyncioTestCase):
    def test_exports(self):
        for name in luduvo.__all__:
            self.assertTrue(hasattr(luduvo, name))
        self.assertTrue(issubclass(luduvo.OAuth2Error, luduvo.LuduvoException))
        self.assertTrue(issubclass(luduvo.TokenPersistenceError, luduvo.LuduvoException))

    async def test_close_preserves_unsaved_tokens(self):
        callback = AsyncMock(side_effect=[RuntimeError(), RuntimeError(), None])
        session = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, json={"token": "new", "refresh_token": "rotated"}
                )
            )
        )
        client = Requests(
            token="old",
            refresh_token="old-refresh",
            session=session,
            on_token_refresh=callback,
        )
        with self.assertRaises(luduvo.TokenPersistenceError):
            await client.refresh()
        with self.assertRaises(luduvo.TokenPersistenceError):
            await client.close()
        self.assertEqual(client.tokens.refresh_token, "rotated")
        await client.close()
        self.assertIsNone(client.tokens)
