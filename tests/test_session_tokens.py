import asyncio
import time
import unittest
from unittest.mock import AsyncMock

import httpx
import jwt

from luduvo import Client, SessionTokens, TokenPersistenceError
from luduvo.utilities.requests import Requests


def token(exp):
    return jwt.encode({"user_id": 42, "username": "test", "role": "player",
                       "token_version": 1, "iat": int(time.time()), "exp": exp},
                      "mock-test-key-not-a-real-secret-123", algorithm="HS256")


class SessionTests(unittest.IsolatedAsyncioTestCase):
    def test_metadata(self):
        tokens = SessionTokens(token(int(time.time()) + 600), "opaque")
        self.assertEqual(tokens.claims.user_id, 42)
        self.assertFalse(tokens.is_expired)
        self.assertIsNotNone(tokens.issued_at)
        self.assertGreater(tokens.expires_in, 0)
        self.assertNotIn("opaque", repr(tokens))
        self.assertIsNone(SessionTokens("opaque").is_expired)
        self.assertTrue(SessionTokens(token(int(time.time()) - 1)).is_expired)

    async def test_concurrent_refresh(self):
        calls = []
        new = token(int(time.time()) + 3600)
        def handler(request):
            calls.append(request.url.path)
            return httpx.Response(200, json={"token": new, "refresh_token": "new"})
        callback = AsyncMock()
        session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        requests = Requests(token=token(int(time.time()) + 30), refresh_token="old",
                            session=session, on_token_refresh=callback)
        try:
            await asyncio.gather(*(requests.ensure_authenticated() for _ in range(5)))
            self.assertEqual(calls, ["/auth/refresh"])
            callback.assert_awaited_once_with(requests.tokens)
        finally:
            await requests.close()

    async def test_persistence_failure(self):
        calls = []
        def handler(request):
            calls.append(request.url.path)
            return httpx.Response(200, json={"token": token(int(time.time()) + 3600),
                                             "refresh_token": "rotated"})
        callback = AsyncMock(side_effect=[RuntimeError("storage failed"), None])
        session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        requests = Requests(token="old", refresh_token="old-refresh", session=session,
                            on_token_refresh=callback)
        try:
            with self.assertRaises(TokenPersistenceError):
                await requests.refresh()
            self.assertEqual(requests.tokens.refresh_token, "rotated")
            await requests.refresh()
            self.assertEqual(calls, ["/auth/refresh"])
            self.assertEqual(callback.await_count, 2)
        finally:
            await requests.close()

    async def test_client_options(self):
        with self.assertRaises(ValueError):
            Client(refresh_margin=-1)
        async with Client(token="opaque", refresh_margin=120) as client:
            self.assertIsNone(client.tokens.claims)
