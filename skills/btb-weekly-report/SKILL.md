---
name: btb-weekly-report
description: "B2B单品牌专卖店(BTB Mono Store)周报与月度MTD销售报告自动化生成专家。参考零售周报标准规范，必须联动 maxcompute-data-agent MCP 工具集(describe_table, execute_sql, search_semantic_catalog, get_dimension_values)从阿里云 MaxCompute 自动化抽取全渠道B2B销售、客流、转化率(CR)、连带率(IPO)、客单价(AOV)、鞋服配品类(APP%/ACC%)占比、月度销售目标达成率(Target Achv%)及期末库存与存销比(MOS)。支持按经销商账户(Account)、门店等级(Store Tier: Chapter/A+/A/B/Outlet)、重装门店(Relo Store)、Top 5可比店与新店多维拆解，并输出对齐管理层标准的 Markdown 周报。触发词：BTB周报, B2B周报, BTB Weekly Report, B2B销售周报, 专卖店周报, MTD周报, 零售周报, 专柜周报, 生成周报, weekly report, btb report."
description_zh: "BTB单品牌专卖店周报/MTD报告生成：销售、客流、转化、品类、库存与目标达成"
description_en: "BTB Mono Store Weekly & MTD Report Generator: Sales, Traffic, CR, Category Mix, Inventory & Target Achievement"
version: 1.0.0
---

# BTB 单品牌专卖店周报与月度 MTD 报告生成专家 (BTB Weekly Report Skill)

本 Skill 用于自动化生成标准规范的 **BTB Mono Store Weekly & MTD Report**（B2B 零售专卖店与专柜周报/月度销售报告）。
输出内容与结构严格对齐品牌零售运营与管理层汇报标准，包含 Key Summary、By Account MTD、By Store Tier、Key Store Review、Relo Store Review、Top 5 Stores 以及 Key Insights。

---

## 核心要求：必须使用 maxcompute-data-agent MCP 工具取数

**生成周报所需的所有底层事实数据，必须严格通过 `maxcompute-data-agent` MCP 工具集从阿里云 MaxCompute 数据库中查询与计算，严禁编造或依赖静态假数据：**

1. **获取最新分区**：在查询分区表（如每日库存表 `dwd_inventory_channel_day`）前，**必须首先调用** `maxcompute-data-agent_describe_table(table_name="dwd_inventory_channel_day")` 确认最新已产出业务分区（如 `pt='20261101'`）。
2. **指标口径与语义对齐**：当需要核准指标公式或维度定义时，优先调用 `maxcompute-data-agent_search_semantic_catalog` 与 `maxcompute-data-agent_get_dimension_values`。
3. **安全执行只读查询**：调用 `maxcompute-data-agent_execute_sql` 执行标准 SELECT 聚合查询。所有针对分区表的查询必须包含分区裁剪条件，且必须遵循业务语义护栏规则（如订单表包含 `status = 'complete'` 或渠道过滤 `channel = 'B2B'`）。

---

## 一、报告标准文风与交付规范 (Report Tone & Guidelines)

1. **客观严谨、数据说话**：所有指标均以事实数仓数据为依据，严禁估算或主观臆造。
2. **结构严格对齐模板**：
   - 顶部邮件头信息（From, Date, Subject, To, Cc）及数据日期区间说明；
   - **【Key Summary】**：核心 KPI 摘要与关键业务定性；
   - **【By Store Tier & Key Store Review】**：分级与核心大店表现摘要；
   - **【Relo Store Review】**：重装重新开业门店追踪；
   - **【Top 5 stores】**：可比老店（Comparable）与新店（New）排名及增幅；
   - **【Key insights】**：四维业务诊断（Sellout, Target Achv%, CR & IPO, APP%）；
   - 对应各章节的 Markdown 数据宽表（替代原始邮件中的图片）；
   - 规范礼貌结语与署名。
3. **颜色与符号标识**：
   - 同比高增长（如 >+50%）及超额达成（>100%）在文字中加粗呈现；
   - 达成率落后时间进度较多或同比下滑明显的店铺明确标注 **（重点关注）**。

---

## 二、业务实体范围与核心指标口径 (Metric System & Business Rules)

### 1. 业务统计实体范围
- **实体对象**：中国大陆 51 家 B2B Mono Brand 专卖店/商场专柜（包含常规加盟店与 1 家 Outlet POP-UP 店），剔除海外/澳门店（如 `C090023982`）。
- **时间周期**：
  - **MTD (Month-To-Date)**：当月 1 日至截止周日（如全月收官为当月 1 日至月末最后一日）。
  - **对比期**：去年同期完整自然月或对应历史周期。

### 2. 核心指标公式与定义

| 指标名称 | 英文标识 | 计算公式 / 业务定义 | 格式 |
| :--- | :--- | :--- | :--- |
| **实付销售额** | Sellout | `SUM(total_paid)`（实收金额） | 货币数值 (元 / M) |
| **规模增长率** | Growth % | `(当期全盘销售额 - 去年同期销售额) / 去年同期销售额` | 百分比 (%) |
| **可比增长率** | Comp Growth % | 仅对两期均在营业的老店统计：`(当期可比销售 - 去年可比销售) / 去年可比销售` | 百分比 (%) |
| **月度目标** | Monthly Target | 预算设定的月度考核目标金额（全国 TTL 86.78M） | 货币数值 (元) |
| **目标达成率** | Target Achv % | `当期销售额 / 月度目标`（对比对应时间进度） | 百分比 (%) |
| **出店客流** | Traffic | 统一以出店人流 `SUM(outqty)` 为基准 | 人次 |
| **成交转化率** | CR | `成单量 (Valid Orders) / 出店客流 (Traffic)` | 百分比 (%) |
| **客单连带件数** | IPO | `销售总件数 (Quantity) / 成单量 (Valid Orders)` | 小数 (如 1.55) |
| **平均客单价** | AOV | `销售总额 (Sellout) / 成单量 (Valid Orders)` | 货币数值 (元) |
| **服装销售占比** | APP % | `服装实付额 (Apparel Sales) / 总销售额 (Sellout)` | 百分比 (%) |
| **配件销售占比** | ACC % | `配件实付额 (Accessories Sales) / 总销售额 (Sellout)` | 百分比 (%) |
| **期末存销比** | MOS | `期末在库总件数 / 当期销售总件数`（折算月度周转月数） | 小数 (如 4.9) |

---

## 三、多维分析架构与汇报层级

### 1. 经销商账户 (By Account) 与主管层级
全国划分为 15 大客户/经销商账户，归属 5 位业务负责人管辖：
1. **David Zhang TTL**：
   - Shanghai Really Group（上海锐力，含苏州比斯特）
   - Shanghai Maoyu Group（上海懋余）
   - Dalian Shangjia Group（大连尚嘉东晨）
2. **Liang Tan TTL**：
   - Taiyuan Hairun Group（太原海润）
   - Jinan xingfeng Group（山东雅元/济南鑫丰）
   - Xi'an Guiming Group（西安桂铭）
3. **Sky Zhang TTL**：
   - Nanchang Chongguang Group（南昌崇光）
   - Xiamen Yueqian Yang Group（厦门越千阳）
   - Chengdu Heli Group（成都赫俪）
   - Chongqing Weige Group（重庆唯格）
   - Kunming Bio Group（云南BIO）
   - Shenzhen Angshoupao Sports Group（深圳热炼/昂首跑）
4. **Gary Pang TTL**：
   - Hefei xinjinhui Group（合肥新锦汇）
5. **Iris Xu TTL**：
   - Tianjin Ruilongxiang Group（天津/北京睿隆祥）
   - Shijiazhuang Jiansheng Group（石家庄健升）

### 2. 门店等级 (Store Tier)
- **Chapter**（1 家）：沈阳万象城旗舰店
- **A+**（6 家）：杭州万象城、南京德基广场、苏州中心、北京SKP、天津万象城、西安万象城
- **A**（32 家）：主流省会与新一线核心标杆店
- **B**（11 家）：重点二线城市专柜/成熟专卖店
- **Outlet**（1 家）：苏州比斯特 POP-UP 店

### 3. 重装改造门店 (Relo Store Review)
重点追踪 2025 年末至 2026 年重新装修/迁址开业的 7 家核心标杆店：
- 沈阳万象城 (Chapter, 2026-05-11)
- 南京德基广场 (A+, 2025-12-31)
- 苏州中心 (A+, 2026-07-15)
- 西安SKP (A, 2026-01-13)
- 成都SKP (A, 2026-04-08)
- 重庆万象城 (B, 2025-11-22)
- 武汉武商广场 (B, 2025-11-19)

---

## 四、MaxCompute 数据抽取 SOP 与底层 SQL 规范

### 1. 核心数据表清单
- **销售宽表**：`dws_fact_channel_store_sales_order_detail`（包含渠道、门店、日期、金额、件数、品类与订单号）
- **客流表**：`dws_fact_b2b_retail_store_traffic`（按 `date_day` 与 `store_code` 统计 `outqty`）
- **库存表**：`dwd_inventory_channel_day`（按最新分区 `pt = 'YYYYMMDD'` 获取日末结余快照）
- **商品维度**：`mdm_dim_product_size_info`（关联 `ean_code` 划分 Shoes, Apparel, Accessories）
- **门店维度**：`mdm_dim_store_info`（获取门店全称、账户归属、开业日期及评级）

### 2. 标准抽取 SQL 模版

#### (1) 销售与品类聚合
```sql
SELECT 
    substr(cast(date as string), 1, 7) as ym,
    store_code,
    sum(total_paid) as sellout,
    sum(case when category = 'Apparel' then total_paid else 0 end) as app_sales,
    sum(case when category = 'Accessories' then total_paid else 0 end) as acc_sales,
    sum(case when category in ('Shoes', 'Footwear') then total_paid else 0 end) as shoes_sales,
    sum(quantity) as qty,
    count(distinct order_number) as orders
FROM dws_fact_channel_store_sales_order_detail
WHERE channel = 'B2B'
  AND store_code != 'C090023982'
  AND ((date >= '{START_DATE}' AND date <= '{END_DATE}') 
    OR (date >= '{LY_START_DATE}' AND date <= '{LY_END_DATE}'))
GROUP BY substr(cast(date as string), 1, 7), store_code;
```

#### (2) 客流聚合
```sql
SELECT 
    substr(cast(date_day as string), 1, 7) as ym,
    store_code,
    sum(outqty) as traffic
FROM dws_fact_b2b_retail_store_traffic
WHERE channel = 'B2B'
  AND ((date_day >= '{START_DATE}' AND date_day <= '{END_DATE}') 
    OR (date_day >= '{LY_START_DATE}' AND date_day <= '{LY_END_DATE}'))
GROUP BY substr(cast(date_day as string), 1, 7), store_code;
```

#### (3) 结余库存聚合
```sql
SELECT 
    i.store_code,
    sum(i.inventory) as total_inv,
    sum(case when p.category in ('Shoes', 'Footwear') then i.inventory else 0 end) as shoes_inv,
    sum(case when p.category = 'Apparel' then i.inventory else 0 end) as app_inv,
    sum(case when p.category = 'Accessories' then i.inventory else 0 end) as acc_inv
FROM dwd_inventory_channel_day i
LEFT JOIN mdm_dim_product_size_info p ON i.sku = p.ean_code
WHERE i.pt = '{LATEST_PT}' AND i.channel = 'B2B'
GROUP BY i.store_code;
```

---

## 五、自动化执行管道与周报生成流程 (SOP)

当触发本 Skill 生成最新报告时，必须严格执行如下标准操作：
1. **确认时间范围与最新分区**：
   - 核查当前日期对应的完整业务自然周（截止周日），确定当月 MTD 统计区间、全月时间进度百分比；
   - 调用 `maxcompute-data-agent_describe_table(table_name="dwd_inventory_channel_day")` 获取最新可用库存业务分区（如 `pt='20261101'`）。
2. **通过 MCP 工具抽取底层数据**：
   - 连续调用 `maxcompute-data-agent_execute_sql` 执行第四节中的三条核心聚合 SQL：
     - ① 销售与品类聚合（当期 MTD vs 去年同期）；
     - ② 门店出店客流聚合（当期 MTD vs 去年同期）；
     - ③ 期末在库结余聚合（最新 pt 分区下的鞋服配库存量）；
     - ④ 门店主数据表 `mdm_dim_store_info`（获取各店等级与开业日期）。
3. **计算多维指标矩阵**：
   - 执行两期店铺交集比对，筛选出可比老店（Comparable Stores）与新开门店（New Stores），分别计算整体增长率与可比增长率；
   - 汇总 15 大客户及 5 大主管 TTL 的各项指标；
   - 汇总 5 大 Store Tier（Chapter, A+, A, B, Outlet）；
   - 提取 7 家 Relo 重装门店表现；
   - 筛选 Comparable Top 5 与 New Top 5。
4. **生成核心业务洞察 (Key Insights)**：
   - **Sellout**：识别同增 >50% 的领跑门店与同比下滑的落后门店；
   - **Target Achv%**：对比时间进度，识别超额完成门店与落后 >10~15 个点的预警门店；
   - **CR & IPO**：识别客流增长但 CR 明显滑落、或 IPO 与 CR 双降的异常门店；
   - **APP%**：梳理服饰占比高增突破店（>30%）与下滑店。
5. **渲染交付标准 Markdown 报告**：落盘保存为 `YYYY.MM.DD BTB Weekly Report.md` 并向用户提供结构化交付说明。
