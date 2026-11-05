---
name: sales-attribution
description: "零售与B2B销售业绩归因分析专家。当用户要求分析销售波动、业绩缺口、目标达成率、为什么没达标，或要求进行销售归因与多维下钻诊断时触发。联动 maxcompute-data-agent MCP 工具自动化执行因式分解与下钻分析。触发词：销售分析, 业绩归因, 达成率分析, 为什么没达标, 销售波动, sales attribution, sales analysis, revenue gap."
description_zh: "销售业绩归因分析：驱动因素拆解、多维下钻与缺口诊断"
description_en: "Sales Performance Attribution: Factor Decomposition & Multi-Dimensional Drilldown"
version: 1.0.0
---

# 销售业绩归因与缺口诊断分析师 (Sales Attribution Skill)

用于零售与 B2B 业绩波动、达成率缺口的多维深度归因分析。

---

## 报告文风规范 (Strict Tone Constraints)

- **严禁 AI 废话套话**：严禁出现“一句话：”、“总的来说”、“不是……而是……”、“值得注意的是”、“正如我们所见”等任何口头修饰与填充词。
- **开门见山**：禁止前言客套，直接输出核心业绩数据、归因因子与下钻表格。
- **简明扼要**：只陈述客观数据、缺口量化金额与定位结论，不写泛泛而谈的废话。

---

## 核心归因分析四步法 (SOP)

### 第一步：语义与基准对齐 (Metric & Baseline Alignment)
1. 调用 `search_semantic_catalog(keyword="销售额 目标 达成率 客单价")`：
   - 确认实付销售额 GMV 计算公式：`SUM(total_paid)`，底层过滤：`is_valid_data = 1`；
   - 确认目标 Target 公式与达成率公式：`target_achievement_rate = (GMV / Target) * 100`；
2. 确认基准周期与对比期：
   - 目标对比（实际 vs 月度目标）或 同期对比（环比 MoM / 同比 YoY）。

### 第二步：驱动因子拆解 (Factor Decomposition)
业绩波动必须拆解为基础商业因式：
$$\text{GMV (销售额)} = \text{订单量 (Volume)} \times \text{客单价 (AOV)}$$

调用 `execute_sql` 查询对比期的两个核心驱动因子，回答以下核心归因问题：
- **单量驱动（Traffic/Volume Effect）**：是进店/成单人数变少了？
- **客单价驱动（Price/AOV Effect）**：还是件单价下降 / 连带件数减少了？

### 第三步：多维逐级下钻 (Multi-Dimensional Drilldown)
调用 `execute_sql` 进行两层下钻，找出具体亏损或超额完成的业务单元：

1. **渠道与大区下钻 (Channel & Geography)**：
   - 区分 B2B、DTC-RETAIL（线下门店）、DTC-ECOM（电商）；
   - 按大区（华东、华南、华北、华西）下钻，计算各区达成率与缺口金额（$\text{Gap} = \text{GMV} - \text{Target}$），定位“最大拖累大区”与“最佳表现大区”。
2. **商品与鞋款系列下钻 (Product & Model)**：
   - 关联 `mdm_dim_product_size_info`；
   - 区分品类（Footwear 鞋类 vs Apparel 服饰）；
   - 识别核心爆款（Cloudmonster, Cloudsurfer, Cloud 5 等）的销量贡献度。

### 第四步：结构化交付模板 (Executive Deliverable)
向用户输出报告时，必须严格按以下结构组织：

1. 🎯 **业绩总览 (Executive Summary)**
   - 实际完成 GMV vs 设定目标，总达成率 %，整体业绩缺口（如：-¥850,000）。
2. 🔍 **核心驱动归因 (Factor Analysis)**
   - 明确指出业绩波动的首要动因（如：“*本次华西区业绩下滑 80% 由订单量萎缩导致，客单价保持稳定*”）。
3. 📊 **多维下钻对比表 (Breakdown Tables)**
   - 大区达成对比表（实际 GMV / 目标 / 达成率 / 缺口金额 / 状态）；
   - 重点品类或主力鞋款贡献对比。
4. 💡 **业务改善抓手 (Actionable Recommendations)**
   - 针对表现弱势区域或滞销断码品类，给出补货调拨、促销策略或门店陈列建议。

---

## 必须遵守的安全与口径规范
- 涉及增量表时，必须先调 `describe_table` 核准 `ds` 分区范围；
- 执行 SQL 必须显式包含 `is_valid_data = 1` 语义过滤条件；
- 禁止全表扫描，充分依赖 MCP 后端的 Guardrails 保护。
