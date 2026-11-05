# MaxCompute Data Agent &bull; 部署与分发指引 (Deployment Guide)

本项目提供两种分发与部署方式，满足不同业务场景：

| 部署模式 | 适用场景 | 使用者体验 | 数仓密钥安全性 |
| :--- | :--- | :--- | :--- |
| **模式 A：中心化云端部署 (推荐)** | 企业 / 团队多人共用（千问办公 / 钉钉 / 协同客户端） | **极简**：用户无需安装 Python，填入 HTTPS 链接直接使用 | **最高**：AccessKey 统一保存在服务端，普通用户无感知 |
| **模式 B：本地分发运行** | 独立分析师或开发者在个人电脑上私有运行 | 用户需在本地运行 Python 或 Docker | 需在用户电脑本地配置 AccessKey |

---

## 模式 A：中心化云端托管部署（推荐 🌟）

只需你在服务器上运行一次容器，团队所有成员即可通过 **SSE 远程连接** 享受 Data Agent。

### 1. 准备配置文件
在服务器上拉取本项目，根据模版创建 `.env`：
```bash
cp .env.example .env
vim .env
```
填写关键参数：
```ini
ALIBABA_CLOUD_ACCESS_KEY_ID=LTAI5t...
ALIBABA_CLOUD_ACCESS_KEY_SECRET=FAot...
MAXCOMPUTE_PROJECT=on_mc_prod
MAXCOMPUTE_ENDPOINT=https://service.cn-shanghai.maxcompute.aliyun.com/api

# 建议配置 Bearer Token 鉴权保护
MCP_AUTH_TOKEN=your_secure_random_token_123456
PORT=8000
```
> 💡 **成本与性能优化**：如果服务器与 MaxCompute 在同一阿里云 Region（如华东 2 上海），将 `MAXCOMPUTE_ENDPOINT` 改为内网地址（`http://service.cn-shanghai.maxcompute.aliyun-inc.com/api`），时延更低且**免公网流量费**。

### 2. 使用 Docker 一键启动
```bash
# 启动服务
docker compose up -d --build

# 查看运行状态
docker compose logs -f
```
服务将在 `http://0.0.0.0:8000/sse` 启动，并自动暴露 5 个统一 MCP Tool。

### 3. 配置域名与 HTTPS 反向代理 (Nginx 示例)
SSE (Server-Sent Events) 需要长连接支持，Nginx 必须开启 `proxy_buffering off`：
```nginx
server {
    listen 443 ssl;
    server_name agent.yourcompany.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 模式 B：分发给别人在本地运行

如果你需要把代码打包给同事，让其在自己电脑上运行：

### 1. 交付物打包
将以下必要文件打包为 `zip` 提供给使用者：
```text
data_agent/
├── server.py              # 服务入口
├── semantic_engine.py     # 业务语义检索
├── guardrails.py          # 成本与安全护栏
├── semantic_layer.yaml    # 指标与维度定义
├── requirements.txt       # 依赖声明
├── .env.example           # 配置模板
├── Dockerfile             # 容器配置
└── docker-compose.yml     # 容器启动文件
```

### 2. 使用者本地启动（方式 1：Docker 一键运行）
使用者解压后执行：
```bash
cp .env.example .env
# 编辑 .env 填入其阿里云密钥
docker compose up -d
```

### 3. 使用者本地启动（方式 2：Python 虚拟环境运行）
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 以本地 stdio 模式供桌面工具连接
python3 server.py --transport stdio
```

---

## 客户端接入指引 (Clients Setup)

不论使用模式 A 还是模式 B，使用者的客户端配置极为简单：

### 1. 千问办公 / 阿里云百炼企业应用接入
1. 进入百炼或千问后台 -> **应用管理** -> **工具中心** -> **添加自定义 MCP 工具**；
2. **协议选择**：`SSE`；
3. **URL 填入**：`https://agent.yourcompany.com/sse`；
4. **鉴权头设置**：
   - Key: `Authorization`
   - Value: `Bearer your_secure_random_token_123456`
5. 保存后系统自动注册 5 个原子工具。

### 2. WorkBuddy AI 客户端接入
打开 `~/.workbuddy-ai/mcp.json`：
- **如果连接云端（模式 A）**：
  ```json
  {
    "mcpServers": {
      "maxcompute-data-agent": {
        "url": "https://agent.yourcompany.com/sse",
        "headers": {
          "Authorization": "Bearer your_secure_random_token_123456"
        }
      }
    }
  }
  ```
- **如果本地运行（模式 B）**：
  ```json
  {
    "mcpServers": {
      "maxcompute-data-agent": {
        "command": "/usr/local/bin/python3",
        "args": ["/path/to/data_agent/server.py", "--transport", "stdio"],
        "env": {
          "ALIBABA_CLOUD_ACCESS_KEY_ID": "...",
          "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "...",
          "MAXCOMPUTE_PROJECT": "on_mc_prod"
        }
      }
    }
  }
  ```

### 3. Claude Desktop / Cursor / VS Code 接入
配置文件路径（如 `claude_desktop_config.json`）：
```json
{
  "mcpServers": {
    "maxcompute-data-agent": {
      "url": "https://agent.yourcompany.com/sse",
      "headers": {
        "Authorization": "Bearer your_secure_random_token_123456"
      }
    }
  }
}
```

---

## 运维与更新指引

- **业务指标或口径调整**：
  只需修改云端服务上的 `semantic_layer.yaml`，重启容器即可，**所有下游使用者的客户端无需任何操作，自动生效最新口径**。
- **监控与排查**：
  查看容器日志即可洞察用户发起的 SQL 查询及 Guardrails 拦截记录：
  ```bash
  docker compose logs -f --tail=100
  ```
