#!/usr/bin/env python3
"""Validate the synthetic order, lead, opportunity and channel-value data model."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
DETAIL_FILE = DATA_DIR / "attribution_detail.json"
REPORT_FILE = DATA_DIR / "data_quality_report.json"
FORBIDDEN_PATTERNS = [r"(?i)internal[-_ ]?(token|endpoint|table)", r"(?i)production[-_ ]?(token|endpoint|table)", r"(?i)channel[-_ ]?code"]
STAGES = ["lead_at", "opportunity_created_at", "opportunity_engaged_at", "store_assigned_at", "appointment_at", "test_drive_at", "deal_at"]
EXPECTED_SOURCES = {"直播间", "私信"}
EXPECTED_ORDER_STATUSES = {"无订单", "未使用", "已核销", "已退款"}
EXPECTED_PROVIDERS = {"服务商 A", "服务商 B", "服务商 C"}
VALUE_BY_CRM_STATE = {
    "无有效历史记录": "新增贡献",
    "历史战败或长期未成交": "战败激活",
    "已有进行中商机或销售跟进": "存量促转",
}
EXPECTED_ACTION_TYPES = {"留资", "团购券购买", "团购券购买 + 留资"}


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def main() -> None:
    records = json.loads(DETAIL_FILE.read_text(encoding="utf-8"))
    errors: list[str] = []
    user_ids = [record["user_id"] for record in records]
    order_ids = [record["order_id"] for record in records if record.get("order_id")]
    if len(user_ids) != len(set(user_ids)):
        errors.append("Duplicate user_id values found.")
    if len(order_ids) != len(set(order_ids)):
        errors.append("Duplicate order_id values found.")

    for record in records:
        touch_at = parse_time(record.get("douyin_touch_at"))
        observation_end = parse_time(record.get("observation_end_at"))
        if not touch_at or not observation_end or touch_at > observation_end:
            errors.append(f"Invalid touch/observation time: {record['user_id']}.")
        previous = None
        for stage in STAGES:
            current = parse_time(record.get(stage))
            if current and previous and current < previous:
                errors.append(f"Invalid stage sequence for {record['user_id']}: {stage} precedes prior stage.")
                break
            if current and observation_end and current > observation_end:
                errors.append(f"Stage after observation end for {record['user_id']}: {stage}.")
                break
            if current:
                previous = current
        lead_at = parse_time(record.get("lead_at"))
        historical_at = parse_time(record.get("historical_opportunity_at"))
        if lead_at and touch_at and lead_at < touch_at:
            errors.append(f"Lead before Douyin touch: {record['user_id']}.")
        if historical_at and touch_at and historical_at >= touch_at:
            errors.append(f"Historical CRM state does not precede touch: {record['user_id']}.")
        if bool(historical_at) != bool(record.get("is_preexisting_opportunity")):
            errors.append(f"Historical opportunity scope mismatch: {record['user_id']}.")
        if record.get("has_order") != bool(record.get("order_id")):
            errors.append(f"Order identity mismatch: {record['user_id']}.")
        if not record.get("has_order") and (record.get("order_at") or record.get("order_status") != "无订单"):
            errors.append(f"Non-order status mismatch: {record['user_id']}.")
        if record.get("has_order") and (not record.get("order_at") or record.get("order_status") == "无订单"):
            errors.append(f"Order status mismatch: {record['user_id']}.")
        if record.get("has_lead") != bool(record.get("lead_id")):
            errors.append(f"Lead identity mismatch: {record['user_id']}.")
        if record.get("is_net_lead") and not record.get("has_lead"):
            errors.append(f"Net-lead scope mismatch: {record['user_id']}.")
        if record.get("has_opportunity") and not record.get("has_lead"):
            errors.append(f"Opportunity without lead: {record['user_id']}.")
        if record.get("has_store_assignment") and not record.get("has_engagement"):
            errors.append(f"Store assignment without opened opportunity: {record['user_id']}.")
        if record.get("has_deal") and not record.get("has_opportunity"):
            errors.append(f"Deal without opportunity: {record['user_id']}.")
        value_type = record.get("conversion_value_type")
        crm_state = record.get("crm_status_before_douyin")
        if bool(record.get("deal_at")) != bool(value_type):
            errors.append(f"Conversion value type mismatch: {record['user_id']}.")
        if crm_state not in VALUE_BY_CRM_STATE:
            errors.append(f"Unexpected CRM status: {record['user_id']}.")
        if value_type and value_type != VALUE_BY_CRM_STATE.get(crm_state):
            errors.append(f"CRM/value mapping mismatch: {record['user_id']}.")
        if record.get("douyin_action_type") not in EXPECTED_ACTION_TYPES:
            errors.append(f"Unexpected Douyin action type: {record['user_id']}.")
        if record.get("source_label") not in EXPECTED_SOURCES:
            errors.append(f"Unexpected source: {record['user_id']}.")
        if record.get("service_provider") not in EXPECTED_PROVIDERS or record.get("settlement_provider") != record.get("service_provider"):
            errors.append(f"Settlement provider mismatch: {record['user_id']}.")
        if not record.get("content_asset"):
            errors.append(f"Content asset missing: {record['user_id']}.")
        if record.get("order_status") not in EXPECTED_ORDER_STATUSES:
            errors.append(f"Unexpected order status: {record['user_id']}.")
        if record.get("has_order") and (record.get("test_drive_at") or record.get("deal_at")) and record.get("order_status") not in {"已核销", "已退款"}:
            errors.append(f"Order user visited or locked without completion/refund status: {record['user_id']}.")
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
            "lifecycle_and_observation_sequence": not any("time" in error.lower() or "sequence" in error.lower() or "Stage after" in error for error in errors),
            "order_and_lead_scope_consistency": not any("mismatch" in error.lower() or "without" in error.lower() for error in errors),
            "crm_value_mapping_consistency": not any("CRM" in error or "Conversion value" in error for error in errors),
            "settlement_provider_consistency": not any("Settlement provider" in error for error in errors),
            "source_action_and_order_status_scope": not any("Unexpected source" in error or "Unexpected Douyin" in error or "Unexpected order" in error for error in errors),
            "content_asset_completeness": not any("Content asset" in error for error in errors),
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
