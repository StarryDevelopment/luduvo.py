import unittest
import httpx

from luduvo import Client


class BulkPresenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_batches_and_missing_users(self):
        calls = []

        def handler(request):
            ids = request.url.params["ids"]
            calls.append(ids)
            return httpx.Response(200, json={"presence": [
                {"user_id": int(ids.split(",")[0]), "state": "online"}
            ]})

        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            )
            result = await client.get_presences([1, 2, 1, 3], batch_size=2)
            self.assertEqual(calls, ["1,2", "3"])
            self.assertEqual([item.user_id for item in result], [1, 3])
            self.assertIsNone(result[0].online)
            self.assertEqual(await client.get_presences([]), [])
