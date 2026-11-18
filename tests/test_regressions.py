import unittest
import httpx

from luduvo import Client
from luduvo.utilities.requests import Requests
from luduvo.utilities.iterators import AsyncPaginator


class RegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_deferred_login(self):
        calls = []

        def handler(request):
            calls.append(request.url.path)
            self.assertEqual(request.url.host, "api.example.test")
            if request.url.path == "/auth/login":
                return httpx.Response(200, json={"token": "test-token", "refresh_token": "refresh"})
            self.assertEqual(request.headers["Authorization"], "Bearer test-token")
            return httpx.Response(200, json={})

        session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        requests = Requests("test", "password", session=session, base_url="example.test")
        try:
            self.assertEqual(calls, [])
            await requests.get("https://api.example.test/me/profile")
            self.assertEqual(calls, ["/auth/login", "/me/profile"])
            self.assertTrue(requests.authenticated)
        finally:
            await requests.close()
        self.assertFalse(requests.authenticated)

    async def test_zero_limit(self):
        async def fetch(offset):
            self.fail("Zero limit must not fetch")

        self.assertEqual(await AsyncPaginator(fetch).limit(0).flatten(), [])

    async def test_token_client(self):
        async with Client(token="test-token") as client:
            self.assertTrue(client.authenticated)
        self.assertFalse(client.authenticated)
