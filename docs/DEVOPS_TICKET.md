# [Service Request] Deploy MaxCompute Data Agent as Cloud MCP Server (SSE) for Qianwen Office Integration

---

## 一、Ticket Summary（工单标题）

**[Service Request] Deploy MaxCompute Data Agent as Cloud MCP Server (SSE) for Qianwen Office Integration**  
*(中文：【服务部署申请】部署 MaxCompute 问数 Agent 云端 MCP 服务（SSE模式），供千问办公全员接入)*

---

## 二、Ticket Description（工单正文）

### 1. 业务背景 (Background & Objective)
我们开发了一套基于 MCP (Model Context Protocol) 协议的 **MaxCompute Data Agent**，为零售运营与分析团队提供自动化业务取数、指标检索与销售周报分析能力。  
目前该服务仅在个人本地环境运行，为了让业务人员在**千问办公（Qianwen Office）**等协同客户端中无需安装 Python 环境、无需接触底层 AccessKey 即可一键接入使用，现需将该 Agent 部署在公司云端服务器/容器集群，并通过 HTTPS 暴露标准的 **SSE (Server-Sent Events)** 端点。

---

### 2. 需要 DevOps 支持的事项 (DevOps Requests)

#### (1) 计算资源与容器运行
- **部署方式**：Docker 容器运行（项目根目录已提供完整的 `Dockerfile` 与 `docker-compose.yml`）。
- **机器规格建议**：**2 Core / 4GB 内存**（轻量级无状态服务）。
- **地域要求（重要）**：建议优先部署在**阿里云华东 2（上海）VPC** 内，可直连 MaxCompute 内网，**免公网流量费**且时延更低。

#### (2) 环境变量与凭证注入 (Environment Variables)
请在部署环境 / 容器编排配置（如 Secret）中注入以下环境变量：
```ini
ALIBABA_CLOUD_ACCESS_KEY_ID=<只读RAM账号AccessKey>
ALIBABA_CLOUD_ACCESS_KEY_SECRET=<只读RAM账号Secret>
MAXCOMPUTE_PROJECT=on_mc_prod

# 阿里云上海内网 Endpoint（如部署在上海 VPC 内部）：
MAXCOMPUTE_ENDPOINT=http://service.cn-shanghai.maxcompute.aliyun-inc.com/api

# MCP 服务端口与鉴权 Token（请 DevOps 团队统一生成高强度随机 Token）
PORT=8000
MCP_AUTH_TOKEN=<DevOps_Generated_Bearer_Token>
```

#### (3) 域名解析与 HTTPS 反向代理 (Nginx / Ingress)
- 申请 / 分配公司内部域名（如 `data-agent.on-running.cn` 或内网可解析域名）。
- 配置 HTTPS 证书并反向代理至容器的 `8000` 端口。
- **关键 Nginx 配置约束（必须开启 SSE 长连接）**：
  ```nginx
  location / {
      proxy_pass http://127.0.0.1:8000;
      proxy_http_version 1.1;
      proxy_set_header Connection '';
      proxy_buffering off;        # 必须关闭缓冲，否则 SSE 数据流无法实时推送
      proxy_cache off;
      proxy_read_timeout 3600s;  # 保障长会话不中断
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
  ```

#### (4) 网络安全与权限控制
- 服务自带 Bearer Token 校验中间件（请求头需携带 `Authorization: Bearer <MCP_AUTH_TOKEN>`）。
- 如有需要，可将域名限制在公司内网 / VPN / 办公网 IP 段访问。

---

### 3. 项目代码与交付物清单 (Artifacts & Files)
- **代码仓库 (Git Repository)**：
  - **URL (HTTPS)**：`https://github.com/yujiexiang-815/maxcompute-data-agent.git`
  - **URL (SSH)**：`git@github.com:yujiexiang-815/maxcompute-data-agent.git`
  - **默认分支**：`main`
- **核心文件与容器配置**：
  - `server.py`：服务启动入口，支持命令：`python server.py --host 0.0.0.0 --port 8000 --transport sse`
  - `Dockerfile` / `docker-compose.yml`：基于 `python:3.11-slim` 构建的容器配置
  - `requirements.txt`：完整的 Python 依赖清单（包含 `mcp`, `pyodps`, `uvicorn`, `starlette` 等）
  - `guardrails.py` & `semantic_layer.yaml`：内置的成本熔断与安全查询护栏

---

### 4. 交付与验收标准 (Acceptance Criteria)

部署完成后，请协助按以下步骤验证验收：
1. **健康检查通过**：
   ```bash
   curl -i https://<分配的域名>/health
   # 预期返回: HTTP 200 OK {"status": "ok", "project": "on_mc_prod"}
   ```
2. **千问办公客户端联调通过**：
   在千问办公的 MCP 扩展中添加远程服务器配置：
   - **名称**：MaxCompute Data Agent
   - **URL**：`https://<分配的域名>/sse`
   - **Header**：`Authorization: Bearer <MCP_AUTH_TOKEN>`
   - 验证可在对话中正常检索指标并执行业务数据查询。
