import unittest
import httpx
from luduvo import Client


class ResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_pagination(self):
        def handler(request):
            self.assertEqual(request.url.path, "/users")
            self.assertEqual(request.url.params["q"], "test")
            offset = int(request.url.params["offset"])
            return httpx.Response(
                200,
                json={
                    "users": [{"id": offset + 1, "username": "test"}],
                    "total": 2,
                },
            )

        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            )
            users = await client.search_users("test", page_size=1).flatten()
            self.assertEqual([user.id for user in users], [1, 2])

    async def test_empty_inventory(self):
        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json={"items": [], "total": 0})
                )
            )
            self.assertEqual(await client.my_inventory().flatten(), [])
