# 自动化看板输出契约

每次运行输出一个 UTF-8 JSON 文件。报告和看板必须读取同一份结构化事实结果，避免两个出口口径不一致。

## 顶层结构

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-09-07_weekly",
  "generated_at": "2026-09-07T08:10:00+08:00",
  "timezone": "Asia/Shanghai",
  "periods": {},
  "data_quality": {},
  "executive_summary": {},
  "metrics": [],
  "anomalies": [],
  "decompositions": [],
  "dimension_impacts": [],
  "drilldowns": [],
  "channel_value": [],
  "strategy_evaluations": [],
  "task_drafts": [],
  "artifacts": {}
}
```

## 周期

```json
{
  "periods": {
    "current": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "baseline": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "observation_cutoff": "YYYY-MM-DD"
  }
}
```

两个周期必须是已结束、等长的完整自然周。

## 数据质量

```json
{
  "data_quality": {
    "status": "pass",
    "data_updated_at": "ISO-8601",
    "checks": [
      {
        "check_id": "source_mapping_rate",
        "status": "pass|warn|block",
        "value": 0.992,
        "threshold": 0.98,
        "message": "来源映射率 99.2%"
      }
    ],
    "blocking_reasons": []
  }
}
```

`status=block` 时，`anomalies`、`decompositions`、`task_drafts` 和 `strategy_evaluations` 必须为空。

## 指标与异常

```json
{
  "metric_id": "opportunity_open_rate",
  "metric_name": "创开率",
  "format": "percent",
  "current": 0.38,
  "baseline": 0.44,
  "absolute_change": -0.06,
  "relative_change": -0.1364,
  "change_unit": "percentage_point",
  "numerator_current": 38,
  "denominator_current": 100,
  "sample_size": 100,
  "is_anomaly": true,
  "threshold_rule": "下降不低于5个百分点且样本不少于20",
  "maturity_rule": null
}
```

异常对象在指标字段基础上追加：

```json
{
  "anomaly_id": "A001",
  "direction": "down",
  "severity": "high|medium|low",
  "business_impact": -6,
  "evidence_level": "fact",
  "summary": "本周创开率下降6个百分点，按当前创建规模估算少开启约6个销售机会"
}
```

## 拆解树

```json
{
  "anomaly_id": "A001",
  "target_metric_id": "opened_opportunity_count",
  "formula": "created_opportunity_count * opportunity_open_rate",
  "method": "symmetric_shapley",
  "target_change": -12,
  "reconciliation_error": 0.01,
  "factors": [
    {
      "factor_id": "opportunity_open_rate",
      "baseline": 0.44,
      "current": 0.38,
      "contribution": -7.1,
      "contribution_share": 0.5917
    }
  ]
}
```

`reconciliation_error` 超过目标变化绝对值的 1% 时标记为数据或计算异常。

## 多维影响

```json
{
  "anomaly_id": "A001",
  "metric_id": "opportunity_open_rate",
  "dimension_name": "region",
  "dimension_value": "华东",
  "current": 0.31,
  "baseline": 0.43,
  "numerator_current": 31,
  "denominator_current": 100,
  "impact": -12,
  "rank_by_abs_impact": 1,
  "sample_passed": true,
  "evidence_level": "fact"
}
```

## 明细下钻

```json
{
  "anomaly_id": "A001",
  "drilldown_type": "created_not_opened_or_over_sla",
  "filters": {
    "region": ["华东"],
    "created_period": ["YYYY-MM-DD", "YYYY-MM-DD"]
  },
  "record_count": 23,
  "fields": ["masked_customer_id", "opportunity_id", "store", "created_at", "wait_hours"],
  "internal_artifact": "details/A001.csv",
  "contains_pii": false
}
```

公开演示数据中 `internal_artifact` 只能指向合成或脱敏明细。

## 渠道价值

```json
{
  "segment": "new|reactivated|assisted_existing",
  "segment_name": "新增贡献",
  "customer_count": 0,
  "customer_share": 0.0,
  "mature_customer_count": 0,
  "lock_rate_30d": 0.0,
  "median_days_to_lock": null,
  "interpretation": "事实性业务解释",
  "causal_claim": false
}
```

## 任务草稿

```json
{
  "task_id": "T001",
  "anomaly_id": "A001",
  "priority": "P1",
  "title": "复核华东重点门店销售机会开启流程",
  "evidence": "华东创开率下降12个百分点，按当前规模少开启约12个销售机会",
  "scope": {"regions": ["华东"], "stores": []},
  "recommended_action": "复核任务提醒、人员排班和抖音来客承接SOP",
  "owner_role": "区域运营/门店负责人",
  "due_date": "YYYY-MM-DD",
  "validation_metrics": ["创开率", "24小时内开启率", "创建至开启时长"],
  "status": "draft",
  "requires_human_approval": true
}
```

## 策略效果

```json
{
  "strategy_id": "SOP_001",
  "strategy_name": "门店承接SOP",
  "launch_date": "YYYY-MM-DD",
  "scope": {},
  "design": "difference_in_differences|pre_post",
  "target_metric": "opportunity_open_rate",
  "estimated_effect": 0.0,
  "effect_unit": "percentage_point",
  "guardrail_metrics": [],
  "evidence_level": "causal_estimate|supported_inference",
  "conclusion": "结论及限制"
}
```

## 输出文件

建议每次运行生成：

```text
outputs/weekly/<current_week_end>/weekly-attribution.json
reports/weekly/<current_week_end>/weekly-attribution.md
details/weekly/<current_week_end>/<anomaly_id>.csv
```

`artifacts` 字段记录实际路径。若平台使用对象存储，则填内部可访问的对象标识，不输出临时签名或个人信息。
