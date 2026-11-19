import unittest
import httpx

from luduvo import Client


class GroupAPITests(unittest.IsolatedAsyncioTestCase):
    async def test_group_metrics_and_presence(self):
        def handler(request):
            if request.url.path == "/me/groups/1/metrics":
                self.assertEqual(request.url.params["range"], "28d")
                return httpx.Response(
                    200,
                    json={
                        "group_id": 1,
                        "range": {},
                        "previous_range": {},
                        "freshness": {},
                        "visits": {"current": 12, "previous": 10},
                        "suppression_threshold": 10,
                    },
                )
            self.assertEqual(request.url.path, "/users/2/presence")
            return httpx.Response(
                200,
                json={
                    "online": True,
                    "state": "online",
                    "joinable": False,
                },
            )

        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            )
            metrics = await client.get_partial_group(1).metrics(range="28d")
            self.assertEqual(metrics.visits.current, 12)
            self.assertIsNone(metrics.visits.percent)
            presence = await client.get_presence(2)
            self.assertEqual(presence.user_id, 2)
            self.assertTrue(presence.online)
