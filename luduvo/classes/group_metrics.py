"""Group analytics response models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricComparison:
    current: float | None
    previous: float | None
    percent: float | None

    @classmethod
    def from_api(cls, data: dict) -> "MetricComparison":
        return cls(data.get("current"), data.get("previous"), data.get("percent"))


@dataclass(frozen=True)
class GroupMetrics:
    group_id: int
    range: dict
    previous_range: dict
    freshness: dict
    data_through_day: int | None
    places: int | None
    live_ccu: int | None
    visits: MetricComparison
    unique_players: MetricComparison
    playtime_hours: MetricComparison
    member_joins_by_day: list[dict]
    members_by_role: list[dict]
    store_revenue_by_item: list[dict]
    ledger_by_type: list[dict]
    payouts_by_role: list[dict]
    suppression_threshold: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "GroupMetrics":
        return cls(
            group_id=data["group_id"],
            range=data["range"],
            previous_range=data["previous_range"],
            freshness=data["freshness"],
            data_through_day=data.get("data_through_day"),
            places=data.get("places"),
            live_ccu=data.get("live_ccu"),
            visits=MetricComparison.from_api(data.get("visits") or {}),
            unique_players=MetricComparison.from_api(data.get("unique_players") or {}),
            playtime_hours=MetricComparison.from_api(data.get("playtime_hours") or {}),
            member_joins_by_day=data.get("member_joins_by_day") or [],
            members_by_role=data.get("members_by_role") or [],
            store_revenue_by_item=data.get("store_revenue_by_item") or [],
            ledger_by_type=data.get("ledger_by_type") or [],
            payouts_by_role=data.get("payouts_by_role") or [],
            suppression_threshold=data.get("suppression_threshold"),
        )
