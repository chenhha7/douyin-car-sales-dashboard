# 模拟数据说明

`data/demo/` 下的文件由 `scripts/generate_demo_data.py` 和 `scripts/transform_data.py` 自动生成，用于公开作品集中的经营看板演示。

## 脱敏与合成原则

- 全部记录通过固定随机种子生成，便于本地复现。
- 用户、订单、线索、商机、历史商机和锁单编号均为合成编号，例如 `DEMO-U00001`。
- 服务商、内容资产、直播间、区域、城市、门店和产品系列均为通用虚构名称。
- 样本量、金额、比例、时间、异常情景和 CRM 历史状态仅用于演示分析逻辑，不代表真实经营表现。
- 仓库不包含生产数据、内部数据表、渠道编码、内部服务地址、日志、凭据或真实个人信息。

## 用户级字段结构

每条记录都包含以下类型的字段：

| 字段类别 | 示例字段 | 用途 |
| --- | --- | --- |
| 抖音触达与行为 | `douyin_touch_at`、`source_label`、`douyin_action_type`、`content_asset`、`live_room` | 区分直播间或私信触达，以及团购券购买 / 留资行为 |
| 团购券订单 | `order_at`、`order_status`、`refund_at`、`paid_amount` | 统计订单、未使用、核销和退款 |
| 内部销售节点 | `lead_at`、`opportunity_created_at`、`opportunity_engaged_at`、`store_assigned_at`、`appointment_at`、`test_drive_at`、`deal_at` | 计算销售漏斗与各环节时效 |
| SOP cohort 标记 | `sop_launch_date`、`sop_status_at_created` | 演示区域门店 SOP 宣贯上线前后的固定 cohort 评估；日期和效果均为合成场景 |
| 触达前 CRM 状态 | `crm_status_before_douyin`、`historical_opportunity_at`、`prior_opportunity_status` | 支撑新增贡献、战败激活和存量促转的价值分层 |
| 归属与结算 | `service_provider`、`settlement_provider`、`region`、`city`、`store`、`product_line` | 支撑服务商结算、直播间复盘和异常下钻 |

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `raw_funnel_records.json` | 合成的原始用户触达、订单、线索、商机、门店承接、到店 / 试驾、锁单与退款事件。 |
| `attribution_detail.json` | 看板使用的用户级明细，补充当前阶段、各环节耗时、成熟商机标记和渠道价值标签。 |
| `attribution_summary.json` | 全局、日度和多维聚合统计，可用于离线检查或扩展其他前端页面。 |
| `weekly_attribution_result.json` | 周度归因 Skill 的完全合成示例输出，用于离线定位 KPI 波动，不在公开看板页面展示。 |
| `data_quality_report.json` | 运行质量与公开发布边界检查后的结果。 |

## 生成与校验

在项目根目录运行：

```bash
python scripts/run_demo.py
```

脚本会重新生成所有文件，并检查主键唯一性、触达与销售阶段顺序、订单 / 线索 / 商机范围一致性、触达前 CRM 状态与渠道价值标签映射、服务商结算归属、合成数据标记和生产信息风险标识。
