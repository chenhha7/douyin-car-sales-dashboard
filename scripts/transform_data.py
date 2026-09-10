#!/usr/bin/env python3
"""Build public dashboard detail and aggregates from synthetic user journeys."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
RAW_FILE = DATA_DIR / "raw_funnel_records.json"
DETAIL_FILE = DATA_DIR / "attribution_detail.json"
SUMMARY_FILE = DATA_DIR / "attribution_summary.json"
MATURE_WINDOW_DAYS = 14


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def hours_between(start: str | None, end: str | None) -> float | None:
    start_time, end_time = parse_time(start), parse_time(end)
    if not start_time or not end_time:
        return None
    return round((end_time - start_time).total_seconds() / 3600, 2)


def safe_rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def average(values: list[float | None]) -> float | None:
    values = [value for value in values if value is not None]
    return round(sum(values) / len(values), 2) if values else None


def median(values: list[float | None]) -> float | None:
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    middle = len(values) // 2
    return round(values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2, 2)


def stage_totals(records: list[dict]) -> dict:
    orders = [record for record in records if record["has_order"]]
    gross_leads = [record for record in records if record["has_lead"]]
    net_leads = [record for record in gross_leads if record["is_net_lead"]]
    created = [record for record in gross_leads if record["has_opportunity"]]
    opened = [record for record in created if record["has_engagement"]]
    assigned = [record for record in opened if record["has_store_assignment"]]
    appointments = [record for record in assigned if record["has_appointment"]]
    test_drives = [record for record in appointments if record["has_test_drive"]]
    deals = [record for record in test_drives if record["has_deal"]]
    unused = [record for record in orders if record["order_status"] == "未使用"]
    verified = [record for record in orders if record["order_status"] == "已核销"]
    refunds = [record for record in orders if record["order_status"] == "已退款"]
    pending_open = [record for record in created if record["is_pending_open"]]
    mature_created = [record for record in created if record["is_mature_opportunity"]]
    mature_opened = [record for record in opened if record["is_mature_open_opportunity"]]
    mature_deals = [record for record in deals if record["is_mature_opportunity"]]
    seven_day_deals = [
        record for record in mature_deals if record["create_to_deal_hours"] is not None and record["create_to_deal_hours"] <= 24 * 7
    ]

    return {
        "orders": len(orders), "gross_leads": len(gross_leads), "net_leads": len(net_leads),
        "created": len(created), "opened": len(opened), "assigned": len(assigned), "appointments": len(appointments),
        "test_drives": len(test_drives), "deals": len(deals), "unused_orders": len(unused),
        "verified_orders": len(verified), "refund_orders": len(refunds), "pending_open": len(pending_open),
        "mature_created": len(mature_created), "mature_opened": len(mature_opened), "mature_deals": len(mature_deals),
        "net_lead_rate": safe_rate(len(net_leads), len(gross_leads)),
        "lead_to_create_rate": safe_rate(len(created), len(gross_leads)),
        "open_rate": safe_rate(len(opened), len(created)),
        "assignment_rate": safe_rate(len(assigned), len(opened)),
        "appointment_rate": safe_rate(len(appointments), len(assigned)),
        "test_drive_rate": safe_rate(len(test_drives), len(appointments)),
        "test_to_deal_rate": safe_rate(len(deals), len(test_drives)),
        "create_to_deal_rate": safe_rate(len(deals), len(created)),
        "open_to_deal_rate": safe_rate(len(deals), len(opened)),
        "mature_create_to_deal_rate": safe_rate(len(mature_deals), len(mature_created)),
        "mature_open_to_deal_rate": safe_rate(len(mature_deals), len(mature_opened)),
        "mature_seven_day_deal_rate": safe_rate(len(seven_day_deals), len(mature_created)),
        "refund_rate": safe_rate(len(refunds), len(orders)),
        "verify_rate": safe_rate(len(verified), len(orders)),
        "average_touch_to_lead_hours": average([record["touch_to_lead_hours"] for record in gross_leads]),
        "average_lead_to_create_hours": average([record["lead_to_create_hours"] for record in created]),
        "average_create_to_open_hours": average([record["create_to_open_hours"] for record in opened]),
        "average_open_to_store_hours": average([record["open_to_store_hours"] for record in assigned]),
        "average_open_to_appointment_hours": average([record["open_to_appointment_hours"] for record in appointments]),
        "average_appointment_to_test_hours": average([record["appointment_to_test_hours"] for record in test_drives]),
        "average_test_to_deal_hours": average([record["test_to_deal_hours"] for record in deals]),
        "average_create_to_deal_hours": average([record["create_to_deal_hours"] for record in mature_deals]),
        "median_create_to_open_hours": median([record["create_to_open_hours"] for record in opened]),
        "median_create_to_deal_hours": median([record["create_to_deal_hours"] for record in mature_deals]),
    }


def dim_summary(records: list[dict], field: str) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record.get(field):
            grouped[record[field]].append(record)
    return [{field: value, **stage_totals(group)} for value, group in sorted(grouped.items())]


def daily_summary(records: list[dict]) -> list[dict]:
    by_day: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record.get("cohort_date"):
            by_day[record["cohort_date"]].append(record)
    return [{"date": date, **stage_totals(group)} for date, group in sorted(by_day.items())]


def build_detail(records: list[dict]) -> list[dict]:
    detail: list[dict] = []
    for record in records:
        row = record.copy()
        cutoff = parse_time(record["observation_end_at"])
        maturity_cutoff = cutoff - timedelta(days=MATURE_WINDOW_DAYS) if cutoff else None
        row["has_opportunity"] = bool(record["opportunity_created_at"])
        row["has_engagement"] = bool(record["opportunity_engaged_at"])
        row["has_store_assignment"] = bool(record["store_assigned_at"])
        row["has_appointment"] = bool(record["appointment_at"])
        row["has_test_drive"] = bool(record["test_drive_at"])
        row["has_deal"] = bool(record["deal_at"])
        row["touch_to_lead_hours"] = hours_between(record["douyin_touch_at"], record["lead_at"])
        row["order_to_lead_hours"] = hours_between(record["order_at"], record["lead_at"])
        row["lead_to_create_hours"] = hours_between(record["lead_at"], record["opportunity_created_at"])
        row["create_to_open_hours"] = hours_between(record["opportunity_created_at"], record["opportunity_engaged_at"])
        row["open_to_store_hours"] = hours_between(record["opportunity_engaged_at"], record["store_assigned_at"])
        row["store_to_appointment_hours"] = hours_between(record["store_assigned_at"], record["appointment_at"])
        row["open_to_appointment_hours"] = hours_between(record["opportunity_engaged_at"], record["appointment_at"])
        row["appointment_to_test_hours"] = hours_between(record["appointment_at"], record["test_drive_at"])
        row["test_to_deal_hours"] = hours_between(record["test_drive_at"], record["deal_at"])
        row["create_to_deal_hours"] = hours_between(record["opportunity_created_at"], record["deal_at"])
        row["is_pending_open"] = bool(row["has_opportunity"] and not row["has_engagement"])
        created_at = parse_time(record["opportunity_created_at"])
        opened_at = parse_time(record["opportunity_engaged_at"])
        row["is_mature_opportunity"] = bool(created_at and maturity_cutoff and created_at <= maturity_cutoff)
        row["is_mature_open_opportunity"] = bool(opened_at and maturity_cutoff and opened_at <= maturity_cutoff)
        row["current_stage"] = (
            "已锁单" if row["has_deal"] else "已试驾" if row["has_test_drive"] else "已预约"
            if row["has_appointment"] else "门店已承接待预约" if row["has_store_assignment"] else "已开启待下发"
            if row["has_engagement"] else "已创建未开启"
            if row["has_opportunity"] else "已留资待创建" if record["has_lead"] else "已退款未留资"
            if record["order_status"] == "已退款" else "订单未留资" if record["has_order"] else "无有效记录"
        )
        detail.append(row)
    return detail


def main() -> None:
    records = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    detail = build_detail(records)
    dimensions = [
        "service_provider", "source_label", "content_asset", "live_room", "order_status", "region", "city", "store",
        "product_line", "conversion_value_type", "crm_status_before_douyin", "douyin_action_type",
    ]
    summary = {
        "metadata": {
            "title": "抖音本地生活卖车经营与渠道价值看板（完全合成数据）",
            "is_synthetic": True,
            "record_count": len(detail),
            "mature_window_days": MATURE_WINDOW_DAYS,
            "observation_end_at": detail[0]["observation_end_at"] if detail else None,
        },
        "overall": stage_totals(detail),
        "daily": daily_summary(detail),
        "dimensions": {field: dim_summary(detail, field) for field in dimensions},
    }
    DETAIL_FILE.write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(detail)} dashboard detail rows: {DETAIL_FILE.relative_to(ROOT)}")
    print(f"Wrote aggregate summary: {SUMMARY_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
