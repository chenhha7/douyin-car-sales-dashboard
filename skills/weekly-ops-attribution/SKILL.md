---
name: weekly-ops-attribution
description: Analyze week-over-week operating metric changes for a funnel-based sales or conversion business. Use when a dashboard, weekly report, or operations review needs a reproducible path from an anomalous KPI to a metric tree, dimension-level impact, record drilldown, task recommendation, and strategy-effect review.
---

# Weekly Operations Attribution

Use this skill to turn a weekly KPI movement into an operational decision loop:

```text
发现问题 → 定位问题 → 下发任务 → 制定策略 → 执行策略 → 效果分析
```

Treat the deterministic pipeline as the fact source. In this repository, read `config/weekly_attribution.json` for rules and `data/demo/weekly_attribution_result.json` for computed results. Read `references/output-schema.md` before producing or validating an output.

## Workflow

1. Validate the input before interpretation.
   - Confirm the payload is marked synthetic for a public demo.
   - Confirm both periods are complete natural weeks, the target metric has a valid denominator, and the metric tree, dimension rows, drilldown, task, and strategy-effect fields are present.
   - Stop and report the data issue if a required field is missing. Do not fill it with an assumption.

2. State the weekly movement in business language.
   - Name the target KPI, prior-week value, current-week value, absolute change, and comparison dates.
   - Explain `销售机会（商机）` once as an internal sales record that has passed an intent assessment; avoid assuming automotive terminology is known.

3. Read the metric tree before dimensions.
   - Use the configured formula only. For example, `开启销售机会数 = 毛线索数 × 线索→创建率 × 创开率`.
   - Rank factors by absolute contribution. Use the precomputed symmetric/Shapley contribution rather than attributing the full KPI change to the last factor examined.
   - Explain whether the movement came primarily from volume or a conversion-efficiency step.

4. Locate the business object through dimension analysis.
   - Follow the configured drill order, usually service provider → live room → region → store → product line.
   - Rank a dimension value by its estimated factor impact, while showing its current and prior denominator/rate.
   - Treat a small denominator as a monitoring signal, not decisive evidence.

5. Drill into action-ready records.
   - Query only records matching the configured drilldown rule, such as created-but-not-opened sales opportunities or records exceeding the creation-to-opening SLA.
   - Keep only the minimum identifiers and fields needed to assign follow-up. Do not expose personal data, production IDs, credentials, or real channel codes in a public artifact.

6. Convert diagnosis into a task.
   - Use the configured playbook’s owner role, action, deadline, focal dimension, and affected-record count.
   - Write the task as an operational instruction, not a vague analytical recommendation.

7. Review strategy effects separately from anomaly diagnosis.
   - Compare pre/post cohorts with the configured windows and maturity rule.
   - Describe the result as an observed pre/post difference. Do not claim causality without a valid control group or experiment.
   - If rollout timing differs by store or region, recommend a staggered rollout or difference-in-differences design for a real evaluation.

## Output Rules

- Lead with the KPI movement and its main driver; then give the dimension, records, owner, action, and verification metric.
- Do not use unavailable platform metrics such as impressions, viewership, or clicks as denominators when only identifiable leads and coupon orders are available.
- Keep settlement/operating ownership separate from channel-value analysis. A service provider can own an attributable entry, while a user may have existed in CRM before the Douyin touchpoint.
- Never turn a correlation, a pre/post comparison, or a synthetic demo result into a confirmed causal statement.
- For public examples, always show the synthetic-data disclaimer.

## Implementation Boundary

The static dashboard must not ask an AI model to calculate attribution in the browser. Generate JSON with deterministic SQL/Python/ETL rules first, then let the page render that JSON. This skill standardizes how an AI agent validates and explains the resulting decision loop.
