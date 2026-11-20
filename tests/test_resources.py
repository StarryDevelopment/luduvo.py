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

    def test_marketplace_wire_fields(self):
        item = Item(None, {"id": 1668, "is_on_sale": 1, "is_limited": 1,
            "has_variants": 0, "asset_type": "face", "rap": 641,
            "limited_quantity": 200, "limited_sold": 0, "owners_count": 145,
            "lowest_resell_price": 1500, "sales_count": 200})
        self.assertIs(item.is_limited, True)
        self.assertIs(item.on_sale, True)
        self.assertIs(item.has_variants, False)
        self.assertEqual(item.rap, 641)
        self.assertEqual(item.limited_quantity, 200)
        self.assertEqual(item.limited_sold, 0)
        self.assertEqual(item.sales, 200)
        self.assertEqual(item.category, "face")
        variant = ItemVariant(None, {"variant_index": 2, "hex_code": "#212121",
            "is_on_sale": True, "price": 0, "thumbnail_key": "item_previews/1721/v2/test.png"}, 1721)
        self.assertEqual(variant.id, 2)
        self.assertEqual(variant.color, "#212121")
        self.assertIs(variant.on_sale, True)
        self.assertEqual(variant.thumbnail_url, "https://assets.luduvo.com/item_previews/1721/v2/test.png")
