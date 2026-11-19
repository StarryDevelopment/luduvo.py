import unittest
import httpx
from luduvo import Client


class PublicAPITests(unittest.IsolatedAsyncioTestCase):
    async def test_aliases_and_missing_total(self):
        calls = []

        def handler(request):
            calls.append(request.url.path)
            return httpx.Response(200, json={"items": [{"id": 1}]})

        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            self.assertEqual(await client.iter_my_inventory().flatten(), [{"id": 1}])
            self.assertEqual(await client.my_inventory().flatten(), [{"id": 1}])
            self.assertEqual(calls, ["/me/inventory", "/me/inventory"])
            with self.assertRaises(ValueError):
                client.iter_my_inventory(page_size=0)

    async def test_categories_remain_list(self):
        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=[{"id": 1}])
            ))
            self.assertEqual(await client.get_store_categories(), [{"id": 1}])

    def test_group_and_user_aliases(self):
        self.assertIs(Client.get_me, Client.get_authenticated_user)
        from luduvo.classes.bases.basegroup import BaseGroup
        from luduvo.classes.bases.baseuser import BaseUser
        self.assertIs(BaseGroup.get_roles, BaseGroup.roles)
        self.assertIs(BaseUser.iter_friends, BaseUser.friends)
