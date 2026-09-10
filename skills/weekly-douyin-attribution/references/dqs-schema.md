# DQS 数据配置

## 必须完成的配置

正式运行前，将以下占位符替换为内部平台真实配置：

```text
mappingName: <DQS_MAPPING_NAME>
tableName: <DQS_TABLE_NAME>
timezone: Asia/Shanghai
grain: 用户ID + 销售机会编码
```

如果一个表不能覆盖完整链路，应明确配置各表及关联键，不得让 Agent 自行猜测表名或关联关系。

## 逻辑字段映射

| 逻辑字段 | DQS 实际字段 | 必需 | 说明 |
| --- | --- | --- | --- |
| customer_id | `<FIELD_CUSTOMER_ID>` | 是 | 脱敏用户标识 |
| order_id | `<FIELD_ORDER_ID>` | 否 | 团购券订单标识 |
| lead_id | `<FIELD_LEAD_ID>` | 是 | 内部线索编码 |
| opportunity_id | `<FIELD_OPPORTUNITY_ID>` | 是 | 销售机会编码 |
| douyin_entry_at | `<FIELD_DOUYIN_ENTRY_AT>` | 是 | 订单或留资入口时间 |
| order_paid_at | `<FIELD_ORDER_PAID_AT>` | 否 | 支付时间 |
| order_status | `<FIELD_ORDER_STATUS>` | 否 | 未使用/已退款/已核销 |
| lead_created_at | `<FIELD_LEAD_CREATED_AT>` | 是 | 线索创建时间 |
| opportunity_created_at | `<FIELD_OPPORTUNITY_CREATED_AT>` | 是 | 销售机会创建时间 |
| opportunity_opened_at | `<FIELD_OPPORTUNITY_OPENED_AT>` | 是 | 销售机会开启时间 |
| store_assigned_at | `<FIELD_STORE_ASSIGNED_AT>` | 否 | 门店下发时间 |
| arrival_at | `<FIELD_ARRIVAL_AT>` | 否 | 到店或试驾时间 |
| lock_at | `<FIELD_LOCK_AT>` | 否 | 锁单时间 |
| lock_status | `<FIELD_LOCK_STATUS>` | 否 | 净锁单/已退单 |
| source_type | `<FIELD_SOURCE_TYPE>` | 是 | 直播间/私信/短视频团购/直播间私信 |
| service_provider | `<FIELD_SERVICE_PROVIDER>` | 是 | 服务商 |
| live_room | `<FIELD_LIVE_ROOM>` | 否 | 直播间或内容资产 |
| region | `<FIELD_REGION>` | 是 | 区域/战区 |
| store | `<FIELD_STORE>` | 是 | 承接门店 |
| product_line | `<FIELD_PRODUCT_LINE>` | 否 | 车系/产品线 |
| crm_status_before_douyin | `<FIELD_PRE_CRM_STATUS>` | 否 | 无历史/历史未成交/进行中 |

## 数据查询要求

每次正式归因至少查询：

1. 当前完整周和基准完整周对应的创建用户组；
2. 覆盖成熟观察窗口所需的后续事件数据；
3. 需要下钻的服务商、直播间、区域、门店和车型字段；
4. 当前活跃策略的范围和上线时间；
5. 数据更新时间和任务批次号。

日期参数建议由定时任务计算后传入：

```text
${current_week_start}
${current_week_end}
${baseline_week_start}
${baseline_week_end}
${observation_cutoff}
```

## 查询输出契约

周度指标查询至少返回：

```text
period_label
metric_name
numerator
denominator
metric_value
sample_size
data_updated_at
```

多维查询至少返回：

```text
period_label
metric_name
dimension_name
dimension_value
numerator
denominator
metric_value
```

明细查询仅返回任务执行所需字段，不返回姓名、手机号等直接个人信息。

## 数据质量阻断条件

满足任一条件时停止经营归因：

- DQS 表或核心字段仍为占位符；
- 当前周或基准周查询为空；
- 数据更新时间早于分析周结束时间；
- 核心事件时间大面积倒序；
- 销售机会开启数大于创建数且无法由跨周期口径解释；
- 来源或门店未映射率超过业务阈值；
- 30 日锁单率未使用成熟用户组。

阻断时生成数据问题报告并通知，不得继续生成业务结论。
