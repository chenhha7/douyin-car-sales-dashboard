#!/usr/bin/env python3
"""Build a weekly attribution, drilldown and action-closure payload from synthetic journeys."""

from __future__ import annotations

import itertools
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
DETAIL_FILE = DATA_DIR / "attribution_detail.json"
OUTPUT_FILE = DATA_DIR / "weekly_attribution_result.json"
CONFIG_FILE = ROOT / "config" / "weekly_attribution.json"


def parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def date_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def records_in_period(records: list[dict], start: date, end: date) -> list[dict]:
    return [record for record in records if record.get("cohort_date") and start <= parse_date(record["cohort_date"]) <= end]


def metrics(records: list[dict]) -> dict:
    gross = [record for record in records if record.get("has_lead")]
    created = [record for record in gross if record.get("has_opportunity")]
    opened = [record for record in created if record.get("has_engagement")]
    assigned = [record for record in opened if record.get("has_store_assignment")]
    appointments = [record for record in assigned if record.get("has_appointment")]
    test_drives = [record for record in appointments if record.get("has_test_drive")]
    deals = [record for record in test_drives if record.get("has_deal")]
    orders = [record for record in records if record.get("has_order")]
    refunds = [record for record in orders if record.get("order_status") == "已退款"]
    return {
        "gross_leads": len(gross),
        "created": len(created),
        "opened": len(opened),
        "assigned": len(assigned),
        "appointments": len(appointments),
        "test_drives": len(test_drives),
        "deals": len(deals),
        "orders": len(orders),
        "refund_orders": len(refunds),
        "lead_to_create_rate": rate(len(created), len(gross)),
        "open_rate": rate(len(opened), len(created)),
        "assignment_rate": rate(len(assigned), len(opened)),
        "appointment_rate": rate(len(appointments), len(assigned)),
        "test_drive_rate": rate(len(test_drives), len(appointments)),
        "test_to_deal_rate": rate(len(deals), len(test_drives)),
        "refund_rate": rate(len(refunds), len(orders)),
    }


def factor_contributions(previous: list[float], current: list[float]) -> list[float]:
    """Order-invariant Shapley contributions for a multiplicative metric tree."""
    count = len(previous)
    totals = [0.0] * count
    for order in itertools.permutations(range(count)):
        values = previous[:]
        before = product(values)
        for index in order:
            values[index] = current[index]
            after = product(values)
            totals[index] += after - before
            before = after
    divisor = float(len(list(itertools.permutations(range(count)))))
    return [value / divisor for value in totals]


def product(values: list[float]) -> float:
    result = 1.0
    for value in values:
        result *= value
    return result


def previous_complete_week(max_date: date) -> tuple[date, date, date, date]:
    """Return current and prior full Monday-Sunday windows."""
    last_sunday = max_date - timedelta(days=(max_date.weekday() + 1) % 7)
    current_start = last_sunday - timedelta(days=6)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=6)
    return current_start, last_sunday, previous_start, previous_end


def dimension_label(field: str) -> str:
    return {
        "service_provider": "服务商",
        "live_room": "直播间",
        "region": "区域",
        "store": "门店",
        "product_line": "产品系列",
    }.get(field, field)


def groups(records: list[dict], field: str) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        value = record.get(field)
        if value:
            result[str(value)].append(record)
    return result


def weekly_dimension_impact(current: list[dict], previous: list[dict], field: str, primary_factor: str) -> list[dict]:
    current_groups, previous_groups = groups(current, field), groups(previous, field)
    values = sorted(set(current_groups) | set(previous_groups))
    rows: list[dict] = []
    for value in values:
        current_metrics = metrics(current_groups.get(value, []))
        previous_metrics = metrics(previous_groups.get(value, []))
        current_rate = current_metrics.get(primary_factor)
        previous_rate = previous_metrics.get(primary_factor)
        current_created = current_metrics["created"]
        impact = None
        if current_rate is not None and previous_rate is not None:
            impact = current_created * (current_rate - previous_rate)
        rows.append({
            "value": value,
            "current": current_metrics,
            "previous": previous_metrics,
            "primary_factor_current": current_rate,
            "primary_factor_previous": previous_rate,
            "estimated_factor_impact": impact,
            "target_delta": current_metrics["opened"] - previous_metrics["opened"],
        })
    return sorted(rows, key=lambda item: abs(item["estimated_factor_impact"] or 0), reverse=True)


def opening_drilldown(records: list[dict], field: str, value: str, sla_hours: int) -> list[dict]:
    result: list[dict] = []
    for record in records:
        if record.get(field) != value or not record.get("has_opportunity"):
            continue
        pending = not record.get("has_engagement")
        over_sla = record.get("create_to_open_hours") is not None and record["create_to_open_hours"] > sla_hours
        if not (pending or over_sla):
            continue
        result.append({
            "user_id": record["user_id"],
            "opportunity_id": record.get("opportunity_id"),
            "service_provider": record.get("service_provider"),
            "live_room": record.get("live_room"),
            "region": record.get("region"),
            "store": record.get("store"),
            "source_label": record.get("source_label"),
            "cohort_date": record.get("cohort_date"),
            "current_stage": record.get("current_stage"),
            "create_to_open_hours": record.get("create_to_open_hours"),
            "reason": "已创建未开启" if pending else f"创建后超过{sla_hours}小时才开启",
        })
    return sorted(result, key=lambda item: item["create_to_open_hours"] or 10**9, reverse=True)[:20]


def strategy_effect(records: list[dict], config: dict) -> dict:
    strategy = config["strategy_registry"][0]
    pre_start, pre_end = (parse_date(value) for value in strategy["pre_period"])
    post_start, post_end = (parse_date(value) for value in strategy["post_period"])

    def cohort_metrics(scope: list[dict]) -> dict:
        created = [record for record in scope if record.get("has_opportunity")]
        d3_opened = [
            record for record in created
            if record.get("create_to_open_hours") is not None and record["create_to_open_hours"] <= 72
        ]
        mature_created = [record for record in created if record.get("is_mature_opportunity")]
        mature_deals = [record for record in mature_created if record.get("has_deal")]
        return {
            "created": len(created),
            "d3_open_rate": rate(len(d3_opened), len(created)),
            "mature_deal_rate": rate(len(mature_deals), len(mature_created)),
        }

    before, after = cohort_metrics(records_in_period(records, pre_start, pre_end)), cohort_metrics(records_in_period(records, post_start, post_end))
    return {
        **strategy,
        "before": before,
        "after": after,
        "d3_open_rate_delta": None if before["d3_open_rate"] is None or after["d3_open_rate"] is None else after["d3_open_rate"] - before["d3_open_rate"],
        "mature_deal_rate_delta": None if before["mature_deal_rate"] is None or after["mature_deal_rate"] is None else after["mature_deal_rate"] - before["mature_deal_rate"],
    }


def main() -> None:
    records = json.loads(DETAIL_FILE.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    max_cohort_date = max(parse_date(record["cohort_date"]) for record in records if record.get("cohort_date"))
    current_start, current_end, previous_start, previous_end = previous_complete_week(max_cohort_date)
    current, previous = records_in_period(records, current_start, current_end), records_in_period(records, previous_start, previous_end)
    tree = config["metric_trees"]["opened"]
    current_metrics, previous_metrics = metrics(current), metrics(previous)
    factor_keys = tree["factors"]
    factor_labels = {
        "gross_leads": "毛线索数",
        "lead_to_create_rate": "线索→创建率",
        "open_rate": "创开率",
    }
    previous_values = [float(previous_metrics[key] or 0) for key in factor_keys]
    current_values = [float(current_metrics[key] or 0) for key in factor_keys]
    contributions = factor_contributions(previous_values, current_values)
    tree_rows = [
        {
            "key": key,
            "label": factor_labels[key],
            "previous": previous_metrics[key],
            "current": current_metrics[key],
            "contribution": round(contributions[index], 3),
            "type": "count" if key == "gross_leads" else "rate",
        }
        for index, key in enumerate(factor_keys)
    ]
    primary_driver = max(tree_rows, key=lambda item: abs(item["contribution"]))
    primary_dimension = tree["primary_dimension"]
    dimension_rows = weekly_dimension_impact(current, previous, primary_dimension, primary_driver["key"])
    top_dimension = dimension_rows[0] if dimension_rows else None
    drilldown = opening_drilldown(current, primary_dimension, top_dimension["value"], config["comparison"]["sla_create_to_open_hours"]) if top_dimension else []
    playbook = config["action_playbook"][tree["playbook"]]
    target_delta = current_metrics["opened"] - previous_metrics["opened"]
    severity = "high" if primary_driver["key"] == "open_rate" and (current_metrics["open_rate"] or 0) < (previous_metrics["open_rate"] or 0) else "medium"
    task = {
        "task_id": f"DEMO-TASK-{current_start.strftime('%G-W%V')}-001",
        "status": "建议下发",
        "owner_role": playbook["owner_role"],
        "deadline": (current_end + timedelta(days=playbook["deadline_days"])).isoformat(),
        "issue": playbook["issue"],
        "action": playbook["action"],
        "focus_dimension": {"type": dimension_label(primary_dimension), "value": top_dimension["value"] if top_dimension else "—"},
        "affected_records": len(drilldown),
    }
    payload = {
        "metadata": {
            "title": "周度经营归因与策略闭环（完全合成数据）",
            "is_synthetic": True,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "rules_version": config["version"],
            "note": "仅展示归因流程、计算结构与交互形式，不代表真实业务诊断、任务或策略效果。",
        },
        "week_comparison": {
            "current": {"start": current_start.isoformat(), "end": current_end.isoformat(), "record_count": len(current)},
            "previous": {"start": previous_start.isoformat(), "end": previous_end.isoformat(), "record_count": len(previous)},
        },
        "anomaly": {
            "metric": "opened",
            "label": tree["label"],
            "severity": severity,
            "current_value": current_metrics["opened"],
            "previous_value": previous_metrics["opened"],
            "delta": target_delta,
            "primary_driver": primary_driver,
            "summary": f"{tree['label']}较前一完整周变化{target_delta:+d}，优先检查{primary_driver['label']}及其影响最大的{dimension_label(primary_dimension)}。",
        },
        "tree": {"formula": tree["formula"], "rows": tree_rows},
        "dimension_analysis": {
            "dimension": primary_dimension,
            "dimension_label": dimension_label(primary_dimension),
            "primary_factor": primary_driver["key"],
            "rows": dimension_rows,
        },
        "drilldown": {
            "rule": tree["drilldown_rule"],
            "label": "已创建未开启或创建→开启超SLA的销售机会",
            "records": drilldown,
        },
        "task": task,
        "strategy_effect": strategy_effect(records, config),
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote weekly attribution payload: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
