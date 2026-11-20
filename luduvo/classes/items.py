"""Typed public Marketplace resources.

Optional fields remain None when absent or not understood. Raw API fields
are retained for consumers while the Marketplace schema evolves.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from ..models import JSONObject, JSONValue
from .bases.baseitem import BaseItem

if TYPE_CHECKING:
    from ..client import Client


def _field(data: JSONObject, *keys: str) -> JSONValue:
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return None


def _text(value: JSONValue) -> str | None:
    return value if isinstance(value, str) else None


def _number(value: JSONValue) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _integer(value: JSONValue) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _boolean(value: JSONValue) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    return None


def _label(value: JSONValue) -> str | None:
    if isinstance(value, dict):
        value = _field(value, "name", "title", "username", "label")
    return _text(value)


class ItemVariant:
    """A Marketplace variant, including color and price when supplied."""

    def __init__(self, client: Client, data: JSONObject, item_id: int):
        self._client = client
        self._data = dict(data)
        self.item_id: int = item_id
        self.variant_index: int | None = _integer(_field(data, "variant_index", "variant_id", "id"))
        self.id: int | None = self.variant_index
        self.name: str | None = _label(_field(data, "name", "title", "color_name", "colour_name"))
        self.color: str | None = _label(_field(data, "hex_code", "color", "colour", "color_hex", "hex"))
        self.hex_code: str | None = _text(data.get("hex_code"))
        self.price: int | float | None = _number(data.get("price"))
        self.thumbnail_key: str | None = _text(data.get("thumbnail_key"))
        self.thumbnail_url: str | None = _text(_field(data, "thumbnail_url", "icon_url", "image_url"))
        self.on_sale: bool | None = _boolean(_field(data, "is_on_sale", "on_sale", "is_for_sale", "for_sale"))
        self.is_on_sale: bool | None = self.on_sale
        if not self.thumbnail_url and self.thumbnail_key:
            from urllib.parse import quote
            parts = self.thumbnail_key.split("/")
            if self.thumbnail_key.startswith("item_previews/") and all(part not in ("", ".", "..") for part in parts):
                self.thumbnail_url = "https://assets.luduvo.com/" + quote(self.thumbnail_key, safe="/")

    @property
    def raw(self) -> JSONObject:
        return dict(self._data)


class Item(BaseItem):
    """Marketplace item or search result; fetch() retrieves full details."""

    def __init__(self, client: Client, data: JSONObject, *, item_id: int | None = None):
        self._client = client
        if isinstance(data.get("item"), dict):
            data = data["item"]
        self._data = dict(data)
        identifier = _integer(_field(data, "id", "item_id"))
        if identifier is None:
            identifier = item_id
        if identifier is None or identifier <= 0:
            raise ValueError("Marketplace item has no valid ID")
        self.id: int = identifier
        self.name: str | None = _text(_field(data, "name", "title"))
        self.description: str | None = _text(data.get("description"))
        self.price: int | float | None = _number(data.get("price"))
        self.sales: int | None = _integer(_field(data, "sales", "sale_count", "sales_count"))
        self.creator_username: str | None = _label(_field(data, "creator_username", "owner_username", "creator", "made_by"))
        self.creator_id: int | None = _integer(_field(data, "creator_id", "owner_id"))
        self.asset_type: str | None = _text(data.get("asset_type"))
        self.slot: str | None = _text(data.get("slot"))
        self.category: str | None = _label(_field(data, "asset_type", "category_name", "category", "type"))
        self.on_sale: bool | None = _boolean(_field(data, "is_on_sale", "on_sale", "is_for_sale", "for_sale"))
        self.is_on_sale: bool | None = self.on_sale
        self.is_limited: bool | None = _boolean(_field(data, "is_limited", "limited"))
        self.has_variants: bool | None = _boolean(data.get("has_variants"))
        self.rap: int | None = _integer(data.get("rap"))
        self.lowest_resell_price: int | None = _integer(data.get("lowest_resell_price"))
        self.limited_quantity: int | None = _integer(data.get("limited_quantity"))
        self.limited_sold: int | None = _integer(data.get("limited_sold"))
        self.owners_count: int | None = _integer(data.get("owners_count"))
        self.thumbs_up: int | None = _integer(data.get("thumbs_up"))
        self.thumbs_down: int | None = _integer(data.get("thumbs_down"))
        self.expires_at: int | None = _integer(data.get("expires_at"))
        self.status: str | None = _text(data.get("status"))
        self.model_url: str | None = _text(data.get("model_url"))
        self.thumbnail_url: str | None = _text(_field(data, "thumbnail_url", "icon_url", "image_url"))
        self.created_at: int | float | None = _number(data.get("created_at"))
        self.updated_at: int | float | None = _number(data.get("updated_at"))

    @property
    def raw(self) -> JSONObject:
        return dict(self._data)

    async def fetch(self) -> Item:
        return await self._client.get_store_item(self.id)

    async def get_variants(self) -> list[ItemVariant]:
        return await self._client.get_item_variants(self.id)
