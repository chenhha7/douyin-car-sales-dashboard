# 模拟数据说明

data/demo/ 下的数据由 scripts/generate_demo_data.py 自动生成，用于展示抖音本地生活卖车场景中的归因与转化漏斗分析。

## 脱敏原则

- 所有记录均为固定随机种子生成的虚构样本。
- 用户、订单、线索、销售机会与成交编号均为合成编号。
- 区域、城市、直播间和产品线均为通用示例名称。
- 指标、金额、样本量和转化率仅用于说明分析逻辑，不代表任何真实经营表现。
- 仓库不包含生产数据、内部数据表、渠道编码、内部服务地址、日志或凭据。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| aw_funnel_records.json | 合成的原始用户事件记录 |
| ttribution_detail.json | 可供看板下钻的用户级归因明细 |
| ttribution_summary.json | 日度和分维度聚合指标 |
| data_quality_report.json | 主键、漏斗与隐私检查结果 |

可以执行 python scripts/run_demo.py 重新生成全部文件。
