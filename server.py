"""MaxCompute Data Agent MCP Server.

Provides Semantic Layer Search, Schema & Partition Metadata, Dimension Enums,
and Safe Guarded SQL Execution for Qianwen Office and other MCP clients.

Supports stdio (local) and SSE (Server-Sent Events for remote / cloud) protocols.
"""

from __future__ import annotations

import argparse
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Ensure user site-packages is included
import site
for p in site.getsitepackages() + [site.getusersitepackages()]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

from mcp.server.mcpserver import MCPServer
from odps import ODPS
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import uvicorn

from guardrails import MaxComputeGuardrail, GuardrailViolation
from semantic_engine import get_semantic_engine

# ------------------------------------------------------------------------------
# 1. Environment & Configuration Loading
# ------------------------------------------------------------------------------
def load_env() -> None:
    """Load variables from .env file if present."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

load_env()

ACCESS_KEY_ID = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
ACCESS_KEY_SECRET = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
PROJECT = os.getenv("MAXCOMPUTE_PROJECT", "on_mc_prod")
ENDPOINT = os.getenv("MAXCOMPUTE_ENDPOINT", "https://service.cn-shanghai.maxcompute.aliyun.com/api")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

# ------------------------------------------------------------------------------
# 2. ODPS Client & Guardrails Singleton
# ------------------------------------------------------------------------------
_odps_client: ODPS | None = None
_partitioned_tables_cache: dict[str, bool] = {}

def get_odps() -> ODPS:
    global _odps_client
    if _odps_client is None:
        if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET:
            raise ValueError(
                "Missing ALIBABA_CLOUD_ACCESS_KEY_ID or ALIBABA_CLOUD_ACCESS_KEY_SECRET in .env"
            )
        _odps_client = ODPS(
            access_id=ACCESS_KEY_ID,
            secret_access_key=ACCESS_KEY_SECRET,
            project=PROJECT,
            endpoint=ENDPOINT,
        )
    return _odps_client

guardrail = MaxComputeGuardrail(default_limit=100, max_limit=1000)
semantic_engine = get_semantic_engine()

def is_table_partitioned(table_name: str) -> bool:
    """Check and cache whether an ODPS table is partitioned."""
    table_lower = table_name.strip().lower()
    if table_lower in _partitioned_tables_cache:
        return _partitioned_tables_cache[table_lower]
    try:
        odps = get_odps()
        if odps.exist_table(table_name):
            tbl = odps.get_table(table_name)
            tbl.reload()
            is_part = bool(tbl.table_schema.partitions)
            _partitioned_tables_cache[table_lower] = is_part
            return is_part
    except Exception:
        pass
    return False

# ------------------------------------------------------------------------------
# 3. FastMCP Definition
# ------------------------------------------------------------------------------
mcp = MCPServer("maxcompute-data-agent")


@mcp.tool()
def search_semantic_catalog(keyword: str, top_k: int = 5) -> dict[str, Any]:
    """根据业务关键词检索指标公式、业务口径、默认过滤条件和底层数据表。
    
    当用户询问指标（如GMV、达成率、售罄率、退款率）或业务实体时，必须优先调用此工具检索对齐口径。

    Args:
        keyword: 业务术语或问题关键词（如 '销售额', '达成率', '门店客流', '退款'）
        top_k: 返回最相关的指标数量（默认 5）
    """
    return semantic_engine.search(keyword, top_k=top_k)


@mcp.tool()
def get_dimension_values(dimension_name: str, field_name: str) -> dict[str, Any]:
    """获取指定维度的标准枚举值及定义，防止大模型对渠道、大区、状态产生幻觉。

    Args:
        dimension_name: 维度模型名称（如 'dim_store', 'dim_product'）
        field_name: 维度字段名称（如 'channel', 'region', 'store_type'）
    """
    return semantic_engine.get_dimension_values(dimension_name, field_name)


@mcp.tool()
def list_tables() -> list[str]:
    """列出当前 MaxCompute 项目下的所有物理表名称。"""
    odps = get_odps()
    return [t.name for t in odps.list_tables()]


@mcp.tool()
def describe_table(table_name: str) -> dict[str, Any]:
    """获取 MaxCompute 物理表的结构定义、字段注释，以及最新可用分区（如 ds/pt）。
    
    在编写包含分区表的 SQL 之前，必须调用此工具确认最新已产出数据的业务分区。

    Args:
        table_name: 物理表名称（如 'dws_fact_retail_sales_order'）
    """
    odps = get_odps()
    if not odps.exist_table(table_name):
        return {"error": f"Table '{table_name}' does not exist in project '{PROJECT}'."}

    table = odps.get_table(table_name)
    table.reload()
    schema = table.table_schema

    columns = [
        {"name": c.name, "type": str(c.type), "comment": c.comment}
        for c in schema.simple_columns
    ]
    partitions = [
        {"name": p.name, "type": str(p.type), "comment": p.comment}
        for p in (schema.partitions or [])
    ]

    recent_partitions: list[str] = []
    is_partitioned = len(partitions) > 0
    _partitioned_tables_cache[table_name.lower()] = is_partitioned

    if is_partitioned:
        try:
            raw_parts = [p.name for p in table.partitions]
            recent_partitions = sorted(raw_parts, reverse=True)[:5]
        except Exception:
            recent_partitions = []

    return {
        "table_name": table.name,
        "comment": table.comment,
        "is_partitioned": is_partitioned,
        "columns": columns,
        "partitions": partitions,
        "recent_partitions": recent_partitions,
    }


@mcp.tool()
def execute_sql(sql: str, max_rows: int = 100) -> dict[str, Any]:
    """在 MaxCompute 中安全执行只读 SELECT 查询，内嵌分区裁剪检查与成本熔断。

    Args:
        sql: 待执行的 SELECT SQL 语句（只读，必须对分区表指定分区过滤条件）
        max_rows: 最大返回行数（默认 100，最高上限 1000）
    """
    # 1. Detect partitioned tables referenced in the SQL
    partitioned_tables_found: list[str] = []
    potential_tables = set(
        part.strip().lower() for part in sys.intern(sql).replace("`", " ").replace(",", " ").split()
    )
    for tbl in potential_tables:
        if is_table_partitioned(tbl):
            partitioned_tables_found.append(tbl)

    # 2. Run Guardrail verification & Limit enforcement
    try:
        rewritten_sql, effective_limit = guardrail.verify_and_prepare_sql(
            sql=sql,
            max_rows=max_rows,
            partitioned_tables=partitioned_tables_found,
            table_default_filters=semantic_engine.table_default_filters
        )
    except GuardrailViolation as gv:
        return {
            "success": False,
            "error_type": "GuardrailViolation",
            "message": str(gv),
            "original_sql": sql,
        }

    # 3. Execute via PyODPS
    try:
        odps = get_odps()
        instance = odps.execute_sql(rewritten_sql)
        results: list[dict[str, Any]] = []

        with instance.open_reader(tunnel=True) as reader:
            for idx, record in enumerate(reader):
                if idx >= effective_limit:
                    break
                row: dict[str, Any] = {}
                for col in reader.schema.columns:
                    val = record[col.name]
                    if hasattr(val, "isoformat"):
                        val = val.isoformat()
                    elif isinstance(val, Decimal):
                        val = float(val)
                    row[col.name] = val
                results.append(row)

        return {
            "success": True,
            "executed_sql": rewritten_sql,
            "row_count": len(results),
            "data": results,
        }
    except Exception as exc:
        return {
            "success": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "executed_sql": rewritten_sql,
        }


# Module level aliases for backward compatibility in Python scripts
get_table_metadata = describe_table
execute_safe_sql = execute_sql
maxcompute_sql_execute = execute_sql


# ------------------------------------------------------------------------------
# 4. Bearer Token Auth Middleware (For SSE Remote Deployment)
# ------------------------------------------------------------------------------
class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only enforce auth if MCP_AUTH_TOKEN is configured
        if MCP_AUTH_TOKEN:
            auth_header = request.headers.get("Authorization", "")
            expected = f"Bearer {MCP_AUTH_TOKEN}"
            # Check authorization header or query param token
            token_param = request.query_params.get("token", "")
            if auth_header != expected and token_param != MCP_AUTH_TOKEN:
                return JSONResponse(
                    {"error": "Unauthorized: Invalid or missing Bearer token"},
                    status_code=401,
                )
        return await call_next(request)


# ------------------------------------------------------------------------------
# 5. Entrypoint: stdio or SSE server
# ------------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="MaxCompute Data Agent MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="MCP Transport protocol: 'stdio' for local CLI/IDE, 'sse' for remote/Qianwen",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Bind host for SSE mode (default 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Bind port for SSE mode (default 8000)",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        print(f"🚀 Starting MaxCompute MCP Server in SSE mode on http://{args.host}:{args.port}/sse")
        if MCP_AUTH_TOKEN:
            print("🔒 Bearer Token authentication is enabled.")
        else:
            print("⚠️ Running without MCP_AUTH_TOKEN. Publicly accessible.")

        app = mcp.sse_app(host=args.host)
        # Attach authentication middleware
        app.add_middleware(TokenAuthMiddleware)
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # stdio mode
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
