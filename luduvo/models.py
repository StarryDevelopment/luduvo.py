"""Public JSON response types; unknown fields remain available."""
from typing import TypeAlias, TypedDict, Literal

JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]
TradeKind: TypeAlias = Literal["received", "sent", "history"]
MetricRange = TypedDict("MetricRange", {"from": int, "to": int, "days": int}, total=False)


class FreshnessInput(TypedDict, total=False):
    name: str
    computed_at: int


class MetricFreshness(TypedDict, total=False):
    computed_at: int
    source: str
    inputs: list[FreshnessInput]


class MembersByRole(TypedDict, total=False):
    name: str
    unique_users: int
