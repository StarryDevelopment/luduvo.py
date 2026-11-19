"""Shared helpers for API resources with offset pagination."""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, TypeVar, overload
from .iterators import AsyncPaginator
from ..models import JSONObject, JSONValue

if TYPE_CHECKING:
    from ..client import Client

T = TypeVar('T')


@overload
def paginate(client: Client, path: str, key: str, page_size: int = 50, *, transform: None = None, **params: str | int) -> AsyncPaginator[JSONObject]: ...
@overload
def paginate(client: Client, path: str, key: str, page_size: int = 50, *, transform: Callable[[JSONObject], T], **params: str | int) -> AsyncPaginator[T]: ...


def paginate(client, path, key, page_size=50, *, transform=None, **params):
    if page_size <= 0:
        raise ValueError("page_size must be positive")

    async def fetch(offset):
        response = await client.requests.get(
            client.url_generator.get_url(path),
            params={**params, "limit": page_size, "offset": offset},
        )
        data = response.json()
        items = data[key]
        if not isinstance(items, list):
            raise ValueError(f"Expected a list in {key}")
        total = data.get("total")
        if total is None:
            total = offset + len(items) + (1 if len(items) >= page_size else 0)
        return {
            "items": [transform(item) for item in items] if transform else items,
            "total": total,
        }

    return AsyncPaginator(fetch)


<<<<<<< HEAD
async def get_json(client, path, **params):
    response = await client.requests.get(
        client.url_generator.get_url(path), params=params
    )
=======
async def get_json(client: Client, path: str, **params: str | int) -> JSONValue:
    response = await client.requests.get(client.url_generator.get_url(path), params=params)
>>>>>>> 422f00ed286d5e82c16e254b4216134daf7ef521
    return response.json()
