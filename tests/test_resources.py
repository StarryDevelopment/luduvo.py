import unittest
import httpx
from luduvo import Client, Item, ItemVariant


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

    async def test_store_search_and_legacy_listing(self):
        def handler(request):
            self.assertEqual(request.url.path, "/store")
            self.assertEqual(request.url.params["limit"], "2")
            if "q" in request.url.params:
                self.assertEqual(request.url.params["q"], "red hat")
                self.assertEqual(request.url.params["sort"], "recent")
                self.assertEqual(request.url.params["made_by"], "42")
            return httpx.Response(200, json={"items": [{"id": 7}], "total": 1})

        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            )
            result = await client.search_store(
                page_size=2, query="red hat", sort="recent", made_by=42
            ).flatten()
            self.assertIsInstance(result[0], Item)
            self.assertEqual(result[0].id, 7)
            self.assertEqual((await client.search_store(2).flatten())[0].id, 7)

    async def test_typed_item_and_variants(self):
        def handler(request):
            if request.url.path == "/store/42":
                return httpx.Response(200, json={"id": 42, "name": "Hat", "price": 0, "on_sale": False, "extra": "retained"})
            self.assertEqual(request.url.path, "/items/42/variants")
            return httpx.Response(200, json={"variants": [{"id": 3, "color": "Blue", "price": 10}]})

        async with Client() as client:
            await client.requests.session.aclose()
            client.requests.session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            item = await client.get_store_item(42)
            self.assertIsInstance(item, Item)
            self.assertEqual(item.name, "Hat")
            self.assertEqual(item.price, 0)
            self.assertIs(item.on_sale, False)
            self.assertEqual(item.raw["extra"], "retained")
            self.assertIsNone(item.sales)
            variants = await item.get_variants()
            self.assertIsInstance(variants[0], ItemVariant)
            self.assertEqual(variants[0].color, "Blue")
            self.assertEqual(variants[0].item_id, 42)
