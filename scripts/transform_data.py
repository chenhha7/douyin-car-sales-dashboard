#!/usr/bin/env python3
"""Build dashboard-ready detail and summary data from synthetic raw records."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
RAW_FILE = DATA_DIR / "raw_funnel_records.json"
DETAIL_FILE = DATA_DIR / "attribution_detail.json"
SUMMARY_FILE = DATA_DIR / "attribution_summary.json"


def parse_day(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def safe_rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def stage_totals(records: list[dict]) -> dict:
    paid = [r for r in records if r["order_status"] != "已退款"]
    leads = [r for r in records if r["lead_date"]]
    qualified = [r for r in records if r["is_qualified_lead"]]
    created = [r for r in records if r["opportunity_created_date"]]
    engaged = [r for r in records if r["opportunity_engaged_date"]]
    test_drives = [r for r in records if r["test_drive_date"]]
    deals = [r for r in records if r["deal_date"]]
    refunds = [r for r in records if r["order_status"] == "已退款"]
    close_days = [
        (parse_day(r["deal_date"]) - parse_day(r["opportunity_created_date"])).days
        for r in deals if r["opportunity_created_date"]
    ]
    return {
        "orders": len(records), "paid_orders": len(paid), "refunds": len(refunds),
        "leads": len(leads), "qualified_leads": len(qualified),
        "opportunity_created": len(created), "opportunity_engaged": len(engaged),
        "test_drives": len(test_drives), "deals": len(deals),
        "refund_rate": safe_rate(len(refunds), len(records)),
        "lead_rate": safe_rate(len(leads), len(paid)),
        "qualified_rate": safe_rate(len(qualified), len(leads)),
        "engagement_rate": safe_rate(len(engaged), len(created)),
        "deal_rate_from_qualified": safe_rate(len(deals), len(qualified)),
        "average_close_days": round(sum(close_days) / len(close_days), 1) if close_days else None,
    }


def dim_summary(records: list[dict], field: str) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record[field]].append(record)
    return [{field: value, **stage_totals(group)} for value, group in sorted(grouped.items())]


def daily_summary(records: list[dict]) -> list[dict]:
    by_day: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    date_map = {
        "orders": "order_date", "leads": "lead_date", "qualified_leads": "lead_date",
        "opportunity_created": "opportunity_created_date", "opportunity_engaged": "opportunity_engaged_date",
        "test_drives": "test_drive_date", "deals": "deal_date", "refunds": "refund_date",
    }
    for record in records:
        for metric, field in date_map.items():
            day = record.get(field)
            if not day:
                continue
            if metric == "qualified_leads" and not record["is_qualified_lead"]:
                continue
            if metric == "refunds" and record["order_status"] != "已退款":
                continue
            by_day[day][metric] += 1
    return [{"date": day, **{metric: values.get(metric, 0) for metric in date_map}} for day, values in sorted(by_day.items())]


def build_detail(records: list[dict]) -> list[dict]:
    detail = []
    for record in records:
        transformed = record.copy()
        transformed["has_lead"] = bool(record["lead_date"])
        transformed["has_opportunity"] = bool(record["opportunity_created_date"])
        transformed["has_engagement"] = bool(record["opportunity_engaged_date"])
        transformed["has_test_drive"] = bool(record["test_drive_date"])
        transformed["has_deal"] = bool(record["deal_date"])
        transformed["close_cycle_days"] = (
            (parse_day(record["deal_date"]) - parse_day(record["opportunity_created_date"])).days
            if record["deal_date"] and record["opportunity_created_date"] else None
        )
        detail.append(transformed)
    return detail


def main() -> None:
    records = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    detail = build_detail(records)
    summary = {
        "metadata": {"title": "抖音本地生活卖车转化看板（模拟数据）", "is_synthetic": True, "record_count": len(detail)},
        "overall": stage_totals(detail), "daily": daily_summary(detail),
        "by_channel": dim_summary(detail, "channel"), "by_region": dim_summary(detail, "region"),
        "by_product_line": dim_summary(detail, "product_line"),
        "by_attribution_type": dim_summary([r for r in detail if r["attribution_type"]], "attribution_type"),
    }
    DETAIL_FILE.write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(detail)} dashboard detail rows: {DETAIL_FILE.relative_to(ROOT)}")
    print(f"Wrote aggregate summary: {SUMMARY_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
