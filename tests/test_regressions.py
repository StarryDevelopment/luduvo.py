import unittest
import httpx

from luduvo import Client
from luduvo.utilities.requests import Requests
from luduvo.utilities.iterators import AsyncPaginator


class RegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_refresh_rotation(self):
        calls = []

        def handler(request):
            calls.append(request.url.path)
            self.assertEqual(request.url.host, "api.example.test")
            if request.url.path == "/auth/refresh":
                import json
                self.assertEqual(json.loads(request.content), {"refresh_token": "old-refresh"})
                return httpx.Response(200, json={"token": "new-token", "refresh_token": "new-refresh"})
            self.assertEqual(request.headers["Authorization"], "Bearer new-token")
            return httpx.Response(200, json={})

        session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        requests = Requests(token="old-token", refresh_token="old-refresh",
                            session=session, base_url="example.test")
        try:
            tokens = await requests.refresh()
            self.assertEqual(tokens.refresh_token, "new-refresh")
            self.assertNotIn("new-token", repr(tokens))
            await requests.get("https://api.example.test/me/profile")
            self.assertEqual(calls, ["/auth/refresh", "/me/profile"])
        finally:
            await requests.close()
        self.assertFalse(requests.authenticated)
        self.assertIsNone(requests.tokens)

    async def test_zero_limit(self):
        async def fetch(offset):
            self.fail("Zero limit must not fetch")

        self.assertEqual(await AsyncPaginator(fetch).limit(0).flatten(), [])

    async def test_token_client(self):
        async with Client(token="test-token") as client:
            self.assertTrue(client.authenticated)
        self.assertFalse(client.authenticated)
