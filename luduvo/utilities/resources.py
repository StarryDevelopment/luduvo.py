"""Shared helpers for API resources with offset pagination."""

from .iterators import AsyncPaginator


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


async def get_json(client, path, **params):
    response = await client.requests.get(
        client.url_generator.get_url(path), params=params
    )
    return response.json()
