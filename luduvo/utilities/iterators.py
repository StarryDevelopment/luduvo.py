"""This module is used internally to provide utilities for iterating over paginated endpoints."""

from typing import Callable, Awaitable, List, TypeVar

T = TypeVar("T")


class Pagination:
    """Utility for paginated endpoints.

    Attributes:
        _fetch_page: A callable that takes limit and offset and returns a dict with "items" and "total".
        limit: The number of items to fetch per page.
    """

    def __init__(
        self,
        fetch_page: Callable[[int, int], Awaitable[dict]],
        limit: int = 50,
    ):
        self._fetch_page = fetch_page
        self.limit = limit

    async def all(self) -> List[T]:
        offset = 0
        results: List[T] = []

        while True:
            data = await self._fetch_page(self.limit, offset)

            items = data["items"]
            total = data["total"]

            results.extend(items)

            offset += self.limit

            if offset >= total or not items:
                break

        return results
