---
name: weekly-ops-attribution
description: Analyze week-over-week operating metric changes for a funnel-based sales or conversion business. Use when a dashboard, weekly report, or operations review needs a reproducible path from an anomalous KPI to a metric tree, dimension-level impact, record drilldown, and a business-verification question without prematurely assigning owners, tasks, or strategies.
---

# Weekly Operations Attribution

Use this skill to turn a weekly KPI movement into a reproducible evidence chain:

```text
发现异动 → 指标拆解 → 多维定位 → 明细核验 → 待业务确认
```

Treat the deterministic pipeline as the fact source. In this repository, read `config/weekly_attribution.json` for rules and `data/demo/weekly_attribution_result.json` for computed results. Read `references/output-schema.md` before producing or validating an output.

## Workflow

1. Validate the input before interpretation.
   - Confirm the payload is marked synthetic for a public demo.
   - Confirm both periods are complete natural weeks, the target metric has a valid denominator, and the metric tree, dimension rows, drilldown, and verification fields are present.
   - Stop and report the data issue if a required field is missing. Do not fill it with an assumption.

2. State the weekly movement in business language.
   - Name the target KPI, prior-week value, current-week value, absolute change, and comparison dates.
   - Explain `销售机会（商机）` once as an internal sales record that has passed an intent assessment; avoid assuming automotive terminology is known.

3. Read the metric tree before dimensions.
   - Use the configured formula only. For example, `开启销售机会数 = 毛线索数 × 线索→创建率 × 创开率`.
   - Rank factors by absolute contribution. Use the precomputed symmetric/Shapley contribution rather than attributing the full KPI change to the last factor examined.
   - Explain whether the movement came primarily from volume or a conversion-efficiency step.

4. Locate the priority verification scope through dimensions.
   - Follow the configured drill order, usually service provider → live room → region → store → product line.
   - Rank a dimension value by its estimated factor impact, while showing its current and prior denominator/rate.
   - Treat a small denominator as a monitoring signal, not decisive evidence.

5. Drill into evidence records.
   - Query only records matching the configured drilldown rule, such as created-but-not-opened sales opportunities or records exceeding the creation-to-opening SLA.
   - Keep only the minimum identifiers and fields needed for business review. Do not expose personal data, production IDs, credentials, or real channel codes in a public artifact.

6. End with a verification question and boundary.
   - State what a business operator should check in the identified scope.
   - Label the conclusion as a priority verification hypothesis, not a confirmed root cause.
   - Do not assign an owner, deadline, task, execution plan, or operating strategy from attribution alone.

## Output Rules

- Lead with the KPI movement and its main contribution factor; then give the priority dimension, evidence records, and verification question.
- Do not use unavailable platform metrics such as impressions, viewership, or clicks as denominators when only identifiable leads and coupon orders are available.
- Keep settlement/operating ownership separate from channel-value analysis. A service provider can own an attributable entry, while a user may have existed in CRM before the Douyin touchpoint.
- Never turn a correlation, a pre/post comparison, or a synthetic demo result into a confirmed causal statement.
- Keep strategy design and strategy-effect evaluation in a separate business-review module after the root cause is confirmed.
- For public examples, always show the synthetic-data disclaimer.

## Implementation Boundary

The static dashboard must not ask an AI model to calculate attribution in the browser. Generate JSON with deterministic SQL/Python/ETL rules first, then let the page render that JSON. This skill standardizes how an AI agent validates and explains the diagnostic evidence chain.
