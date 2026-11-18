import unittest
import httpx

from luduvo.utilities.requests import Requests
from luduvo.utilities.exceptions import TooManyRequests


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_retry(self):
        calls = []

        def handler(request):
            calls.append(request.method)
            if len(calls) == 1:
                return httpx.Response(429, headers={"Retry-After": "0"})
            return httpx.Response(200, json={})

        requests = Requests(session=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        try:
            await requests.get("https://api.luduvo.com/test")
            self.assertEqual(calls, ["GET", "GET"])
        finally:
            await requests.close()

    async def test_mutation_not_retried(self):
        calls = []

        def handler(request):
            calls.append(request.method)
            return httpx.Response(429, headers={"Retry-After": "0"})

        requests = Requests(session=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        try:
            with self.assertRaises(TooManyRequests):
                await requests.post("https://api.luduvo.com/test")
            self.assertEqual(calls, ["POST"])
        finally:
            await requests.close()

    async def test_foreign_origin_rejected(self):
        requests = Requests(token="test")
        try:
            with self.assertRaises(ValueError):
                await requests.get("https://example.org")
        finally:
            await requests.close()
