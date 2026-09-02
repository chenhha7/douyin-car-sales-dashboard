#!/usr/bin/env python3
"""Validate funnel sequencing and check that generated demo data remains synthetic."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
DETAIL_FILE = DATA_DIR / "attribution_detail.json"
REPORT_FILE = DATA_DIR / "data_quality_report.json"
FORBIDDEN_PATTERNS = [
    r"(?i)internal[-_ ]?(token|endpoint|table)",
    r"(?i)production[-_ ]?(token|endpoint|table)",
    r"(?i)channel[-_ ]?code",
]
STAGES = ["order_date", "lead_date", "opportunity_created_date", "opportunity_engaged_date", "test_drive_date", "deal_date"]


def parse_day(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def main() -> None:
    records = json.loads(DETAIL_FILE.read_text(encoding="utf-8"))
    errors: list[str] = []
    for key in ["user_id", "order_id"]:
        values = [record[key] for record in records]
        if len(values) != len(set(values)):
            errors.append(f"Duplicate {key} values found.")

    for record in records:
        previous = None
        for stage in STAGES:
            current = parse_day(record.get(stage))
            if current and previous and current < previous:
                errors.append(f"Invalid stage sequence for {record['user_id']}: {stage} precedes prior stage.")
                break
            if current:
                previous = current
        if record["order_status"] == "已退款" and record.get("lead_date"):
            errors.append(f"Refunded order enters funnel: {record['user_id']}.")
        if bool(record.get("deal_date")) != bool(record.get("attribution_type")):
            errors.append(f"Attribution type mismatch: {record['user_id']}.")
        if not record.get("is_synthetic"):
            errors.append(f"Non-synthetic marker missing: {record['user_id']}.")

    payload = json.dumps(records, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, payload, flags=re.IGNORECASE):
            errors.append(f"Forbidden production-like marker found: {pattern}")

    report = {
        "status": "passed" if not errors else "failed",
        "record_count": len(records),
        "checks": {
            "unique_user_and_order_ids": not any("Duplicate" in error for error in errors),
            "stage_sequence": not any("stage sequence" in error for error in errors),
            "refunds_excluded_from_funnel": not any("Refunded order" in error for error in errors),
            "attribution_consistency": not any("Attribution type" in error for error in errors),
            "synthetic_data_markers": not any("Non-synthetic" in error for error in errors),
            "production_marker_scan": not any("Forbidden" in error for error in errors),
        },
        "errors": errors,
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
