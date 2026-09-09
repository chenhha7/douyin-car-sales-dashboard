# Weekly attribution output contract

Read this reference when generating, validating, or explaining a weekly attribution payload.

## Required top-level fields

```text
metadata.is_synthetic              boolean; must be true for the public demo
week_comparison.current            {start, end, record_count}
week_comparison.previous           {start, end, record_count}
anomaly                            target KPI movement and primary driver
tree                               configured formula and factor contributions
dimension_analysis                 ranked values for the next drilldown layer
drilldown.records                  action-ready records matching the rule
task                               owner, deadline, focal object, and action
strategy_effect                    cohort-based pre/post review
```

## Interpretation fields

| Section | Minimum fields | Interpretation boundary |
| --- | --- | --- |
| `anomaly` | `label`, `previous_value`, `current_value`, `delta`, `primary_driver` | Describe the weekly movement, not a root cause by itself. |
| `tree.rows` | `label`, `previous`, `current`, `contribution`, `type` | Contributions must reconcile approximately to the target delta. |
| `dimension_analysis.rows` | `value`, current/prior metrics, `estimated_factor_impact` | Use for priority ranking; check sample size before action. |
| `drilldown.records` | synthetic user/opportunity ID, focal dimensions, current stage, SLA duration, reason | Use to create follow-up, never expose real personal data. |
| `task` | owner role, issue, action, deadline, focus dimension | Convert the diagnosis into an accountable next step. |
| `strategy_effect` | pre/post windows, cohort size, target metrics, note | Report as a pre/post observation unless a control design exists. |

## Recommended answer structure

1. **发现**：`[KPI]` in `[current week]` changed from `[prior]` to `[current]`.
2. **拆解**：The largest negative/positive factor was `[factor]`, contributing approximately `[x]` target units.
3. **定位**：`[dimension value]` had the largest estimated effect; cite its two-period rate and denominator.
4. **下钻**：`[n]` records meet `[drilldown rule]` and require review.
5. **动作**：Assign `[owner]` to `[action]` by `[deadline]`; track `[verification metric]`.
6. **复盘**：Describe the configured pre/post cohort change and its causal limitation.
