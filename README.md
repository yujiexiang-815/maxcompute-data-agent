# MaxCompute Data Agent (MCP Server & Retail Analytics)

基于 **Model Context Protocol (MCP)** 的阿里云 MaxCompute 智能数据分析 Agent。结合数仓语义层（Semantic Layer）与安全成本护栏，为**千问办公（通义千问企业版 / 钉钉千问）**、**Claude**、**OpenCode** 等协同客户端提供自动化指标问数、全渠道零售分析以及销售周报生成能力。

---

## 🌟 核心特性

- **协议兼容**：支持标准 MCP 协议，提供 `stdio`（本地终端/客户端）与 `SSE`（云端远程长连接）双传输模式。
- **业务语义层 (Semantic Layer)**：基于 `semantic_layer.yaml` 定义销售、客流、转化率(CR)、客单价(AOV)、连带率(IPO)、鞋服配品类结构与库存指标。
- **安全与成本熔断护栏 (Guardrails)**：强制分区裁剪、只读权限白名单校验、敏感表脱敏与查询行数限制，防止意外全表扫描与大模型幻觉。
- **内置数据分析技能库 (Agent Skills)**：
  - `btb-weekly-report`：自动化出具 B2B 专卖店周报 / MTD 销售达成报告。
  - `sales-attribution`：业绩波动归因、多维下钻与缺口诊断。
  - `store-traffic-funnel`：门店客流捕获率与转化漏斗分析。

---

## 📁 目录结构

```text
data_agent/
├── server.py              # MCP Server 核心入口 (支持 stdio 与 SSE 模式)
├── chat.py                # 本地终端交互式千问问数命令行 (CLI)
├── semantic_engine.py     # 业务语义检索与口径对齐引擎
├── semantic_layer.yaml    # 零售与 B2B 全渠道核心指标与维度模型定义
├── guardrails.py          # 成本熔断与只读 SQL 语义护栏
├── test_agent.py          # 核心工具链单元测试
├── Dockerfile             # 容器镜像构建配置
├── docker-compose.yml     # 一键容器化运行编排
├── requirements.txt       # Python 依赖清单
├── .env.example           # 环境变量配置模板
│
├── skills/                # 自动化数据分析技能库 (Skills)
│   ├── btb-weekly-report/ # B2B 单品牌专卖店周报/MTD 报告自动化技能
│   │   ├── SKILL.md       # 技能 SOP 与取数口径规范
│   │   └── run_report.py  # 周报自动化数据提取与渲染脚本
│   ├── sales-attribution/ # 销售业绩归因分析专家
│   └── store-traffic-funnel/ # 门店客流转化漏斗分析
│
├── reports/               # 周报交付件与归档数据
│   ├── 2026.11.01 BTB Weekly Report.md # 最新周周报交付成品
│   ├── 2026.10.25 BTB Weekly Report.eml # 业务原始邮件模版
│   └── assets/            # 周报历史报表底图
│
└── docs/                  # 部署与架构说明文档
    ├── DEVOPS_TICKET.md   # DevOps 云端部署工单申请模板 (Ticket)
    ├── DEPLOYMENT.md      # 云端容器与反向代理部署指引
    ├── README_QIANWEN.md  # 千问办公平台 MCP 接入指南
    ├── architecture.html  # 架构设计交互图
    └── index.html         # 系统概览页面
```

---

## 🚀 快速启动

### 1. 环境准备
```bash
# 克隆代码
git clone git@github.com:yujiexiang-815/maxcompute-data-agent.git
cd maxcompute-data-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env
```

配置 `.env` 关键参数：
```ini
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
MAXCOMPUTE_PROJECT=on_mc_prod
MAXCOMPUTE_ENDPOINT=https://service.cn-shanghai.maxcompute.aliyun.com/api

# 如对接千问模型 CLI (可选)
BAILIAN_API_KEY=sk-xxxxxx
BAILIAN_MODEL=qwen-plus
```

### 2. 运行单测验证连通性
```bash
python3 test_agent.py
```

### 3. 启动 MCP 服务

- **本地 Stdio 模式**（供 OpenCode / Claude Desktop / Cursor 本地使用）：
  ```bash
  python3 server.py --transport stdio
  ```

- **远程 SSE 模式**（供千问办公 / 云端多端接入）：
  ```bash
  export MCP_AUTH_TOKEN="your_secure_bearer_token"
  python3 server.py --transport sse --host 0.0.0.0 --port 8000
  ```

- **Docker 一键启动**：
  ```bash
  docker compose up -d --build
  ```

---

## 🛠️ MCP 核心工具清单 (Exposed Tools)

服务向大模型客户端暴露 5 个只读安全数据工具：

1. `search_semantic_catalog`：根据业务关键词检索指标公式、业务口径、默认过滤条件和底层数据表。
2. `get_dimension_values`：获取渠道、大区、门店等级的标准枚举值，防止模型幻觉。
3. `list_tables`：列出当前项目下的可用业务物理表清单。
4. `describe_table`：获取表结构字段注释及最新可用业务分区（如 `pt='20261101'`）。
5. `execute_sql`：安全执行只读 SELECT 查询，内嵌分区裁剪检查与成本熔断。

---

## 📊 零售周报自动化 (BTB Weekly Report)

本项目内置完整的 BTB 零售周报生成器：
- **执行逻辑**：读取 `skills/btb-weekly-report/SKILL.md`，通过 `run_report.py` 自动化从 MaxCompute 抽取全量 51 家专卖店数据。
- **输出成果**：生成对齐管理层标准的 Markdown 周报（如 `reports/2026.11.01 BTB Weekly Report.md`），覆盖 Sellout、Target Achv%、CR、IPO、AOV、APP%、ACC%、MOS 及重点关注门店下钻分析。

---

## ☁️ 云端部署 (Deployment)

如需将本 Agent 部署为常驻云服务并接入千问办公：
- 参考 **[DevOps 提单模板](docs/DEVOPS_TICKET.md)** 直接提单给运维团队；
- 详细 Nginx SSE 长连接反代与环境变量配置请参阅 **[部署指南](docs/DEPLOYMENT.md)**。
