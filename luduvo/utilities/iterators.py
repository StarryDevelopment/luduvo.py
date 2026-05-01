"""This module is used internally to provide utilities for iterating over paginated endpoints."""

from typing import Callable, AsyncIterator, TypeVar, Generic, Awaitable

T = TypeVar("T")


class AsyncPaginator(Generic[T]):
    def __init__(self, fetch_page: Callable[[int], Awaitable[dict]]):
        self._fetch_page = fetch_page
        self._limit = None

    def limit(self, value: int) -> "AsyncPaginator[T]":
        self._limit = value
        return self

    async def flatten(self) -> list[T]:
        results: list[T] = []
        async for item in self:
            results.append(item)
        return results

    async def first(self) -> T | None:
        async for item in self:
            return item
        return None

    def __aiter__(self) -> AsyncIterator[T]:
        return self._iterator()

    async def _iterator(self) -> AsyncIterator[T]:
        offset = 0
        fetched = 0

        while True:
            page = await self._fetch_page(offset)

            items: list[T] = page.get("items", [])
            total: int = page.get("total", 0)

            if not items:
                break

            for item in items:
                yield item
                fetched += 1

                if self._limit is not None and fetched >= self._limit:
                    return

            offset += len(items)

            if offset >= total:
                break
