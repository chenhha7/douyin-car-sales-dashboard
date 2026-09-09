#!/usr/bin/env python3
"""Generate a fully synthetic, user-level demo of Douyin local-life car sales."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "demo" / "raw_funnel_records.json"
SEED = 20260906
OBSERVATION_END = datetime(2026, 9, 9, 23, 59)
SOP_LAUNCH_DATE = datetime(2026, 7, 14, 0, 0)

# The source structure follows the reviewed business framing: live rooms are the
# main scale driver; direct messages are smaller but receive a higher share of
# qualified follow-up. Names and values below are entirely synthetic.
SOURCES = [
    {
        "name": "直播间",
        "weight": 0.76,
        "order_rate": 0.72,
        "lead_rate": 0.96,
        "net_rate": 0.31,
        "create_rate": 0.46,
        "open_rate": 0.36,
        "appointment_rate": 0.66,
        "test_rate": 0.62,
        "deal_rate": 0.35,
    },
    {
        "name": "私信",
        "weight": 0.24,
        "order_rate": 0.03,
        "lead_rate": 0.99,
        "net_rate": 0.24,
        "create_rate": 0.36,
        "open_rate": 0.64,
        "appointment_rate": 0.60,
        "test_rate": 0.60,
        "deal_rate": 0.22,
    },
]

SERVICE_PROVIDERS = [
    {"name": "服务商 A", "weight": 0.39, "open_adjustment": 0.03, "deal_adjustment": 0.02},
    {"name": "服务商 B", "weight": 0.35, "open_adjustment": -0.04, "deal_adjustment": -0.01},
    {"name": "服务商 C", "weight": 0.26, "open_adjustment": 0.00, "deal_adjustment": -0.02},
]
PROVIDER_ASSETS = {
    "服务商 A": ["直播间 A-午场", "直播间 A-晚场"],
    "服务商 B": ["直播间 B-午场", "直播间 B-晚场"],
    "服务商 C": ["直播间 C-午场", "直播间 C-晚场"],
}
REGIONS = {
    "区域 A": {"城市 A1": ["演示门店 A1-1", "演示门店 A1-2"], "城市 A2": ["演示门店 A2-1", "演示门店 A2-2"]},
    "区域 B": {"城市 B1": ["演示门店 B1-1", "演示门店 B1-2"], "城市 B2": ["演示门店 B2-1", "演示门店 B2-2"]},
    "区域 C": {"城市 C1": ["演示门店 C1-1", "演示门店 C1-2"], "城市 C2": ["演示门店 C2-1", "演示门店 C2-2"]},
    "区域 D": {"城市 D1": ["演示门店 D1-1", "演示门店 D1-2"], "城市 D2": ["演示门店 D2-1", "演示门店 D2-2"]},
}
SOP_EFFECT_BY_REGION = {
    "区域 A": {"open": 0.18, "assign": 0.06, "appointment": 0.08, "deal": 0.05, "fast_weight": 0.84},
    "区域 B": {"open": 0.15, "assign": 0.05, "appointment": 0.06, "deal": 0.04, "fast_weight": 0.78},
    "区域 C": {"open": 0.12, "assign": 0.04, "appointment": 0.05, "deal": 0.03, "fast_weight": 0.72},
    "区域 D": {"open": 0.09, "assign": 0.03, "appointment": 0.04, "deal": 0.02, "fast_weight": 0.68},
}
PRODUCTS = [
    {"name": "产品系列 A", "weight": 0.42, "open_adjustment": 0.02, "deal_adjustment": 0.02},
    {"name": "产品系列 B", "weight": 0.34, "open_adjustment": -0.04, "deal_adjustment": -0.03},
    {"name": "产品系列 C", "weight": 0.24, "open_adjustment": 0.00, "deal_adjustment": 0.00},
]

# These labels describe the CRM state *before* the Douyin touch. They are used
# only on the value-analysis page, not as a replacement for the sales funnel.
CRM_STATES = [
    {
        "name": "无有效历史记录",
        "weight": 0.34,
        "value_type": "新增贡献",
        "create_adjustment": 0.00,
        "deal_multiplier": 0.70,
        "historical_status": None,
    },
    {
        "name": "历史战败或长期未成交",
        "weight": 0.18,
        "value_type": "战败激活",
        "create_adjustment": 0.04,
        "deal_multiplier": 1.40,
        "historical_status": "战败 / 长期未成交",
    },
    {
        "name": "已有进行中商机或销售跟进",
        "weight": 0.48,
        "value_type": "存量促转",
        "create_adjustment": 0.07,
        "deal_multiplier": 1.80,
        "historical_status": "进行中商机 / 销售跟进",
    },
]


def choose(rng: random.Random, items: list[dict]) -> dict:
    return rng.choices(items, weights=[item["weight"] for item in items], k=1)[0]


def iso(value: datetime | None) -> str | None:
    return value.isoformat(timespec="minutes") if value else None


def day(value: datetime | None) -> str | None:
    return value.date().isoformat() if value else None


def clamp(value: float) -> float:
    return max(0.01, min(0.98, value))


def before_observation(value: datetime | None) -> datetime | None:
    return value if value and value <= OBSERVATION_END else None


def generate_records(sample_size: int = 1200) -> list[dict]:
    rng = random.Random(SEED)
    start = datetime(2026, 5, 28, 9, 0)
    records: list[dict] = []

    for index in range(1, sample_size + 1):
        source = choose(rng, SOURCES)
        provider = choose(rng, SERVICE_PROVIDERS)
        product = choose(rng, PRODUCTS)
        crm_state = choose(rng, CRM_STATES)
        touch_at = start + timedelta(days=rng.randrange(104), hours=rng.randrange(12), minutes=rng.randrange(60))
        region = rng.choice(list(REGIONS))
        city = rng.choice(list(REGIONS[region]))
        store = rng.choice(REGIONS[region][city])
        late_period = touch_at.date() >= datetime(2026, 7, 1).date()
        store_issue = store == "演示门店 C2-2" and late_period
        provider_issue = provider["name"] == "服务商 B" and source["name"] == "直播间" and late_period

        has_order = rng.random() < source["order_rate"]
        has_lead = rng.random() < source["lead_rate"]
        order_at = touch_at if has_order else None
        lead_at = touch_at + timedelta(minutes=rng.randint(2, 120)) if has_lead else None
        is_net_lead = bool(has_lead and rng.random() < source["net_rate"])

        refund_rate = 0.11 + (0.10 if provider_issue else 0.0)
        refunded = bool(has_order and rng.random() < refund_rate)
        refund_at = before_observation(order_at + timedelta(hours=rng.randint(2, 72))) if refunded else None
        if refunded and not refund_at:
            refunded = False
        order_status = "无订单" if not has_order else "已退款" if refunded else "未使用"

        prior_opportunity_at = None
        if crm_state["historical_status"]:
            history_days = rng.randint(45, 200) if crm_state["value_type"] == "战败激活" else rng.randint(5, 120)
            prior_opportunity_at = touch_at - timedelta(days=history_days, hours=rng.randint(0, 23))

        created_at = opened_at = store_assigned_at = appointment_at = test_at = deal_at = None
        if has_lead and rng.random() < clamp(source["create_rate"] + crm_state["create_adjustment"]):
            created_at = before_observation(lead_at + timedelta(minutes=rng.randint(15, 1_440)))
            if created_at:
                sop_effect = SOP_EFFECT_BY_REGION[region] if created_at >= SOP_LAUNCH_DATE else None
                open_rate = source["open_rate"] + provider["open_adjustment"] + product["open_adjustment"]
                if store_issue:
                    open_rate -= 0.18
                if provider_issue:
                    open_rate -= 0.10
                if sop_effect:
                    open_rate += sop_effect["open"]
                if rng.random() < clamp(open_rate):
                    fast_weight = sop_effect["fast_weight"] if sop_effect else 0.55
                    open_delay = rng.choices(
                        [rng.randint(10, 240), rng.randint(241, 2_880)], weights=[fast_weight, 1 - fast_weight], k=1
                    )[0]
                    opened_at = before_observation(created_at + timedelta(minutes=open_delay))
                    assign_rate = 0.91 - (0.10 if store_issue or provider_issue else 0.0)
                    if sop_effect:
                        assign_rate += sop_effect["assign"]
                    if opened_at and rng.random() < clamp(assign_rate):
                        store_assigned_at = before_observation(opened_at + timedelta(hours=rng.randint(1, 36)))
                    appointment_rate = source["appointment_rate"] + (sop_effect["appointment"] if sop_effect else 0.0)
                    if store_assigned_at and rng.random() < clamp(appointment_rate):
                        appointment_at = before_observation(store_assigned_at + timedelta(hours=rng.randint(4, 72)))
                        if appointment_at and rng.random() < source["test_rate"]:
                            test_at = before_observation(appointment_at + timedelta(hours=rng.randint(8, 144)))
                            if test_at:
                                deal_rate = (
                                    source["deal_rate"] + provider["deal_adjustment"] + product["deal_adjustment"]
                                ) * crm_state["deal_multiplier"]
                                if sop_effect:
                                    deal_rate += sop_effect["deal"]
                                if rng.random() < clamp(deal_rate):
                                    deal_at = before_observation(
                                        test_at + timedelta(days=rng.randint(2, 7), hours=rng.randint(0, 12))
                                    )

        if has_order and not refunded and (appointment_at or test_at or deal_at or rng.random() < 0.28):
            order_status = "已核销"

        action_type = "团购券购买 + 留资" if has_order and has_lead else "团购券购买" if has_order else "留资"
        room = rng.choice(PROVIDER_ASSETS[provider["name"]]) if source["name"] == "直播间" else None
        content_asset = room if room else f"{provider['name']} · 私信内容"

        records.append({
            "user_id": f"DEMO-U{index:05d}",
            "order_id": f"DEMO-O{index:05d}" if has_order else None,
            "lead_id": f"DEMO-L{index:05d}" if has_lead else None,
            "opportunity_id": f"DEMO-CASE{index:05d}" if created_at else None,
            "deal_id": f"DEMO-D{index:05d}" if deal_at else None,
            "historical_opportunity_id": f"DEMO-HIST{index:05d}" if prior_opportunity_at else None,
            "douyin_touch_at": iso(touch_at),
            "order_at": iso(order_at),
            "lead_at": iso(lead_at),
            "opportunity_created_at": iso(created_at),
            "opportunity_engaged_at": iso(opened_at),
            "store_assigned_at": iso(store_assigned_at),
            "appointment_at": iso(appointment_at),
            "test_drive_at": iso(test_at),
            "deal_at": iso(deal_at),
            "refund_at": iso(refund_at),
            "historical_opportunity_at": iso(prior_opportunity_at),
            "observation_end_at": iso(OBSERVATION_END),
            "sop_launch_date": day(SOP_LAUNCH_DATE),
            "sop_status_at_created": "宣贯后" if created_at and created_at >= SOP_LAUNCH_DATE else "宣贯前" if created_at else None,
            "touch_date": day(touch_at),
            "order_date": day(order_at),
            "lead_date": day(lead_at),
            "opportunity_created_date": day(created_at),
            "opportunity_engaged_date": day(opened_at),
            "store_assigned_date": day(store_assigned_at),
            "appointment_date": day(appointment_at),
            "test_drive_date": day(test_at),
            "deal_date": day(deal_at),
            "refund_date": day(refund_at),
            "cohort_date": day(touch_at),
            "has_order": has_order,
            "has_lead": has_lead,
            "is_net_lead": is_net_lead,
            "order_status": order_status,
            "source_label": source["name"],
            "douyin_action_type": action_type,
            "service_provider": provider["name"],
            "settlement_provider": provider["name"],
            "content_asset": content_asset,
            "live_room": room,
            "region": region,
            "city": city,
            "store": store,
            "product_line": product["name"],
            "crm_status_before_douyin": crm_state["name"],
            "prior_opportunity_status": crm_state["historical_status"],
            "is_preexisting_opportunity": bool(prior_opportunity_at),
            "conversion_value_type": crm_state["value_type"] if deal_at else None,
            "paid_amount": rng.choice([199, 299, 399, 499]) if has_order else None,
            "is_synthetic": True,
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic conversion-operation records.")
    parser.add_argument("--size", type=int, default=1200)
    args = parser.parse_args()
    records = generate_records(args.size)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(records)} synthetic records: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
