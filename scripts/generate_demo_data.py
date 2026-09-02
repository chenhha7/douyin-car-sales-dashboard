#!/usr/bin/env python3
"""Generate deterministic, fully synthetic funnel data for the public demo."""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "demo" / "raw_funnel_records.json"
SEED = 20260902

CHANNELS = [
    {"name": "直播内容入口", "weight": 0.48, "lead_rate": 0.78, "qualified_rate": 0.58, "engage_rate": 0.61, "deal_rate": 0.27},
    {"name": "短视频内容入口", "weight": 0.24, "lead_rate": 0.66, "qualified_rate": 0.47, "engage_rate": 0.52, "deal_rate": 0.21},
    {"name": "搜索内容入口", "weight": 0.16, "lead_rate": 0.70, "qualified_rate": 0.53, "engage_rate": 0.57, "deal_rate": 0.24},
    {"name": "私信内容入口", "weight": 0.12, "lead_rate": 0.73, "qualified_rate": 0.55, "engage_rate": 0.59, "deal_rate": 0.25},
]
REGIONS = {
    "区域 A": ["城市 A1", "城市 A2"],
    "区域 B": ["城市 B1", "城市 B2"],
    "区域 C": ["城市 C1", "城市 C2"],
    "区域 D": ["城市 D1", "城市 D2"],
}
PRODUCTS = ["产品系列 A", "产品系列 B", "产品系列 C"]
LIVE_ROOMS = ["演示直播间 A", "演示直播间 B", "演示直播间 C"]


def choose_weighted(rng: random.Random, items: list[dict]) -> dict:
    return rng.choices(items, weights=[item["weight"] for item in items], k=1)[0]


def iso(day: date | None) -> str | None:
    return day.isoformat() if day else None


def generate_records(sample_size: int = 720) -> list[dict]:
    rng = random.Random(SEED)
    start = date(2026, 4, 1)
    records: list[dict] = []

    for index in range(1, sample_size + 1):
        channel = choose_weighted(rng, CHANNELS)
        order_day = start + timedelta(days=rng.randrange(84))
        region = rng.choice(list(REGIONS))
        city = rng.choice(REGIONS[region])
        product = rng.choices(PRODUCTS, weights=[0.42, 0.34, 0.24], k=1)[0]
        room = rng.choice(LIVE_ROOMS) if channel["name"] == "直播内容入口" else "非直播入口"

        refunded = rng.random() < 0.12
        order_status = "已退款" if refunded else ("已核销" if rng.random() < 0.43 else "已支付")
        refund_day = order_day + timedelta(days=rng.randint(0, 4)) if refunded else None

        lead_day = None
        qualified = False
        opportunity_created_day = None
        opportunity_engaged_day = None
        test_drive_day = None
        deal_day = None
        attribution_type = None

        if not refunded and rng.random() < channel["lead_rate"]:
            lead_day = order_day + timedelta(days=rng.randint(0, 2))
            qualified = rng.random() < channel["qualified_rate"]
            if qualified:
                opportunity_created_day = lead_day + timedelta(days=rng.randint(0, 2))
                if rng.random() < channel["engage_rate"]:
                    opportunity_engaged_day = opportunity_created_day + timedelta(days=rng.randint(0, 3))
                    if rng.random() < 0.69:
                        test_drive_day = opportunity_engaged_day + timedelta(days=rng.randint(1, 6))
                        if rng.random() < channel["deal_rate"]:
                            deal_day = test_drive_day + timedelta(days=rng.randint(1, 11))
                            attribution_type = rng.choices(
                                ["新增获客", "存量激活", "辅助转化"],
                                weights=[0.34, 0.47, 0.19],
                                k=1,
                            )[0]

        records.append({
            "user_id": f"DEMO-U{index:05d}",
            "order_id": f"DEMO-O{index:05d}",
            "lead_id": f"DEMO-L{index:05d}" if lead_day else None,
            "opportunity_id": f"DEMO-CASE{index:05d}" if opportunity_created_day else None,
            "deal_id": f"DEMO-D{index:05d}" if deal_day else None,
            "order_date": iso(order_day),
            "lead_date": iso(lead_day),
            "opportunity_created_date": iso(opportunity_created_day),
            "opportunity_engaged_date": iso(opportunity_engaged_day),
            "test_drive_date": iso(test_drive_day),
            "deal_date": iso(deal_day),
            "refund_date": iso(refund_day),
            "order_status": order_status,
            "is_qualified_lead": qualified,
            "channel": channel["name"],
            "live_room": room,
            "region": region,
            "city": city,
            "product_line": product,
            "paid_amount": rng.choice([199, 299, 399, 499]),
            "attribution_type": attribution_type,
            "is_synthetic": True,
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic funnel records.")
    parser.add_argument("--size", type=int, default=720)
    args = parser.parse_args()
    records = generate_records(args.size)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(records)} synthetic records: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
