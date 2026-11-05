# 千问办公 MaxCompute Data Agent 接入指南

本指南指导您将 MaxCompute MCP 服务以 **SSE 远程协议** 对接到**千问办公（通义千问企业版 / 阿里云百炼应用 / 钉钉千问）**，让企业用户在办公对话框中直接用自然语言进行智能数据分析。

---

## 一、 快速启动 MCP 服务

### 1. 本地 stdio 模式（供 OpenCode / VS Code 本地使用）
```bash
python3 server.py --transport stdio
```

### 2. 远程 SSE 模式（供千问办公云端对接）
启动 HTTP/SSE 服务（默认监听 `8000` 端口）：
```bash
# 建议配置 MCP_AUTH_TOKEN 鉴权保护
export MCP_AUTH_TOKEN="your-secure-token-123456"
python3 server.py --transport sse --port 8000
```
启动成功日志：
```text
🚀 Starting MaxCompute MCP Server in SSE mode on http://0.0.0.0:8000/sse
🔒 Bearer Token authentication is enabled.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 二、 公网网络连通方案

千问办公作为云端 SaaS 服务，需要能够访问您的 SSE 端点：

### 方案 A：本地测试（使用 Cloudflare Tunnel 快速穿透，免费免配置）
```bash
# 如果安装了 cloudflared
cloudflared tunnel --url http://localhost:8000
```
会生成公网临时 HTTPS 地址，例如：
`https://random-subdomain.trycloudflare.com/sse`

### 方案 B：生产环境（推荐部署在阿里云 FC 3.0 或 SAE）
- **同 VPC 直连**：部署在华东 2（上海）VPC 内，使用 MaxCompute 内网 Endpoint，查询无公网流量费且延迟最低。
- **自带 HTTPS**：阿里云函数计算直接分配公网触发器 URL。

---

## 三、 千问办公 / 百炼平台智能体配置

### 1. 添加 MCP 工具
进入**千问企业版管理后台**或**阿里云百炼控制台 -> 我的应用 / 智能体 -> 工具中心**：
1. 点击 **「添加自定义 MCP 工具」**。
2. **传输协议**：选择 `SSE (Server-Sent Events)`。
3. **SSE 端点 URL**：填写您的公网服务地址，例如：
   `https://agent.yourcompany.com/sse`
4. **认证方式**：
   - 选择 `Header 认证`。
   - Key: `Authorization`
   - Value: `Bearer your-secure-token-123456`
5. 点击 **「保存并测试连通」**，平台将自动发现 5 个核心 Tool：
   - `search_semantic_catalog`：业务口径与指标检索
   - `get_dimension_values`：渠道/大区标准枚举值查询
   - `list_tables`：列出项目下所有物理表名
   - `describe_table`：表结构定义与最新业务分区查询
   - `execute_sql`：只读执行与成本护栏（自动 LIMIT、防全表扫描）

---

### 2. 配置智能体 Prompt（System Instruction）

在千问办公的智能体角色设定（Prompt）中，粘贴以下 SOP 指引，确保大模型严格遵守执行纪律：

```markdown
你是一个顶级的企业级 MaxCompute 数据分析专家。
你的职责是帮助企业员工通过自然语言准确、高效、安全地分析全渠道零售、B2B、库存与门店业务数据。

### 【文风规范（Strict Report Style）】
- 严禁 AI 废话套话：禁止使用“一句话总结：”、“总的来说”、“不是……而是……”、“值得注意的是”等修饰填充词。
- 开门见山：禁止前言客套铺垫，直接陈述数据事实、表格与量化差距。
- 简明报告：输出简明高管简报，数据严谨，杜绝空话。

### 【工具调度 SOP 工作流（必须严格遵循）】
当用户提出业务问数需求时，严格按以下 4 步执行：

1. 【语义对齐】：
   遇到具体业务指标（如 GMV、销售额、达成率、售罄率、退款率等）或维度，优先调用 `search_semantic_catalog` 检索标准计算公式、底层物理表及默认过滤条件（如 `is_valid_data = 1`）。
   涉及枚举疑问时，调用 `get_dimension_values` 确认；探索表名时调用 `list_tables`。

2. 【分区感知】：
   若涉及分区表，必须先调用 `describe_table` 查询该表**最新已产出的分区**（如 `pt` 或 `ds`）。
   严格禁止编写不带分区条件的查询，杜绝全表扫描。

3. 【SQL 编写与安全执行】：
   - 编写只读 SELECT 语句，在 WHERE 条件中同时包含分区条件与语义层给出的 default_filter。
   - 调用 `execute_sql` 执行。
   - 系统会自动应用 LIMIT 保护机制。若报错提示缺少分区，请根据报错补充后重试。

4. 【业务归因与洞察呈现】：
   - 直接给出精炼的核心数据结论。
   - 如果数据包含多维度或趋势，必须使用 Markdown 表格呈现。
   - 在回答最后，注明数据来源表、统计口径公式以及查询的业务日期范围。
```

---

## 四、 本地全链路测试方法

在提交千问办公前，可在本地运行自带的单元与功能集成测试：

```bash
python3 -m unittest test_agent.py
```

测试覆盖了指标检索、维度枚举、分区表检测、DDL 拦截、分区漏写拦截与真实 MaxCompute SQL 链路。
