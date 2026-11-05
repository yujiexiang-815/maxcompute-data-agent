---
name: store-traffic-funnel
description: "门店客流与转化率漏斗分析专家。当用户要求分析门店客流、进店率、客流转化率 CR、进店人流波动或漏斗转化时触发。联动 maxcompute-data-agent MCP 工具自动化提取客流与交易数据并输出极简商业简报。触发词：门店客流, 进店率, 转化率分析, 客流漏斗, CR, store traffic, conversion rate, funnel."
description_zh: "门店客流漏斗与转化率分析：路过客流、进店率、成单转化率与瓶颈诊断"
description_en: "Store Traffic Funnel & Conversion Analysis"
version: 1.0.0
---

# 门店客流漏斗与转化率分析 (Store Traffic Funnel Skill)

用于分析零售实体门店从“路过”到“成交”的完整客流漏斗。

---

## 报告文风规范 (Strict Tone Constraints)

- **严禁 AI 废话套话**：禁止出现“一句话总结：”、“总的来说”、“不是……而是……”、“值得注意的是”、“正如我们所见”等任何口头修饰。
- **开门见山**：不写前言铺垫，直接呈现核心数据指标与结构化表格。
- **事实与数据说话**：文字只陈述数据事实、环比/同比变动幅度与归因定位，不讲空泛理论。

---

## 4 级漏斗标准指标与口径

调用 `search_semantic_catalog` 与 `describe_table` 核对以下口径：

| 漏斗层级 | 业务指标 | 物理字段 / 取数来源 | 转化率定义 |
| :--- | :--- | :--- | :--- |
| **L1 路过客流** | `pass_by_traffic` | `dws_fact_b2b_retail_store_traffic.passby` | 基准客流基数 |
| **L2 进店客流** | `out_store_traffic` | `dws_fact_b2b_retail_store_traffic.outqty` (以出店人流统计) | **进店率 (Capture Rate)** = L2 / L1 |
| **L3 成交单量** | `valid_transactions` | `dws_fact_retail_sales_order.valid_transaction_count` | **成交转化率 (CR)** = L3 / L2 |
| **L4 实付业绩** | `gmv` | `dws_fact_retail_sales_order.total_paid` (带 `is_valid_data=1`) | **客单价 (AOV)** = L4 / L3 |

---

## 执行步骤 (Execution Flow)

1. **口径与最新分区获取**：
   - 调 `describe_table("dws_fact_b2b_retail_store_traffic")` 确认客流表结构（全量事实表，按 `date_day` 或 `date` 过滤）。
   - 调 `describe_table("dws_fact_retail_sales_order")` 确认订单表结构及最新分区。
2. **提取漏斗数据**：
   - 调用 `execute_sql` 关联门店主数据 `mdm_dim_store_info`、客流表 `dws_fact_b2b_retail_store_traffic` 与零售订单表。
   - 按门店或大区聚合 `passby`, `outqty`, `valid_transaction_count`, `total_paid`。
3. **定位漏斗瓶颈**：
   - **进店率低（L2/L1 < 8%）**：橱窗陈列、门店入口吸引力或商圈位置问题；
   - **成交率低（L3/L2 < 12%）**：店内动线、导购接待、尺码缺货或货品组合问题；
   - **客单价低（L4/L3）**：连带销售不足、主推高单价鞋款占比低。

---

## 输出报告模板 (Deliverable Format)

输出必须按照以下极简结构交付：

### 1. 核心指标快报
| 指标 | 本期数值 | 同期/基准对比 | 波动幅度 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| 路过客流 (Pass-by) | xx 人次 | xx 人次 | +x% / -x% | 正常/异常 |
| 进店客流 (Traffic) | xx 人次 | xx 人次 | +x% / -x% | 正常/异常 |
| 进店捕获率 (Capture Rate) | xx.x% | xx.x% | +x.x pt | 正常/异常 |
| 客流成交转化率 (CR) | xx.x% | xx.x% | +x.x pt | 正常/异常 |
| 客单价 (AOV) | ¥xx | ¥xx | +x% / -x% | 正常/异常 |

### 2. 门店下钻漏斗表
（按成交转化率 CR 从低到高排序，高亮后 3 家需重点改善门店）
| 门店名称 | 进店客流 | 成交笔数 | 转化率 (CR) | 进店率 | 实付 GMV | 瓶颈判定 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

### 3. 瓶颈定位与改善抓手
- **瓶颈门店**：直接列出具体店名及具体受损指标（如：*门店 A 进店客流达 1.2 万人但 CR 仅 6.8%，低于均值 5.4 个百分点*）。
- **执行动作**：1~2 条具体业务动作（如：*核查门店 A 热销鞋码断码率，优化中岛陈列与试穿连带话术*）。
