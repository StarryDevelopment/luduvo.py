import hashlib
import base64
import json
import unittest
from urllib.parse import urlsplit, parse_qs

import httpx
from luduvo import OAuth2Client, OAuth2Error


class OAuthTests(unittest.IsolatedAsyncioTestCase):
    async def test_flow(self):
        def handler(request):
            if request.url.path == "/oauth/token":
                payload = json.loads(request.content)
                self.assertEqual(payload["code_verifier"], auth.verifier)
                self.assertEqual(payload["grant_type"], "authorization_code")
                self.assertNotIn("Authorization", request.headers)
                return httpx.Response(200, json={"access_token": "test-token"})
            self.assertEqual(request.url.path, "/oauth/userinfo")
            self.assertEqual(request.headers["Authorization"], "Bearer test-token")
            return httpx.Response(200, json={"id": 7, "sub": "7", "username": "test"})

        async with OAuth2Client("app", "https://example.org/callback",
                                transport=httpx.MockTransport(handler)) as client:
            auth = client.authorize()
            query = parse_qs(urlsplit(auth.url).query)
            expected = base64.urlsafe_b64encode(
                hashlib.sha256(auth.verifier.encode()).digest()
            ).rstrip(b"=").decode()
            self.assertEqual(query["code_challenge"], [expected])
            with self.assertRaises(OAuth2Error):
                await client.exchange("code", "wrong", auth)
            token = await client.exchange("code", auth.state, auth)
            self.assertNotIn("test-token", repr(token))
            self.assertEqual((await client.userinfo(token)).id, 7)
