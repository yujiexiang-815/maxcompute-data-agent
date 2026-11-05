"""Local Interactive Qianwen Data Agent CLI.

Simulates Qianwen Office (千问办公) Agent experience locally using DashScope / Bailian API.
Runs full ReAct loop with the 4 MaxCompute MCP tools.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import requests

from server import (
    search_semantic_catalog,
    get_dimension_values,
    list_tables,
    describe_table,
    execute_sql,
)

# ------------------------------------------------------------------------------
# 1. Load Environment
# ------------------------------------------------------------------------------
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY")
MODEL_NAME = os.getenv("BAILIAN_MODEL", "qwen-plus")

if not BAILIAN_API_KEY:
    print("❌ Error: BAILIAN_API_KEY not found in .env")
    sys.exit(1)

# ------------------------------------------------------------------------------
# 2. Tool Definitions for Qwen (OpenAI-compatible format)
# ------------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_semantic_catalog",
            "description": "根据业务关键词检索指标公式、业务口径、默认过滤条件和底层数据表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "业务术语或问题关键词，如 '销售额', '达成率', '库存', '退款'",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回最相关的数量，默认 5",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dimension_values",
            "description": "获取指定维度的标准枚举值及定义，防止大模型对渠道、大区、状态产生幻觉。",
            "parameters": {
                "type": "object",
                "properties": {
                    "dimension_name": {
                        "type": "string",
                        "description": "维度模型名称，如 'dim_store', 'dim_product'",
                    },
                    "field_name": {
                        "type": "string",
                        "description": "维度字段名称，如 'channel', 'region', 'store_type'",
                    },
                },
                "required": ["dimension_name", "field_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "列出当前 MaxCompute 项目下的所有物理表名称。",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "获取 MaxCompute 物理表的结构定义、字段注释，以及最新可用分区（如 pt 或 ds）。在写含分区表的 SQL 前必须调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "物理表名，如 'dws_fact_retail_sales_order', 'mdm_dim_store_info'",
                    }
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "在 MaxCompute 中安全执行只读 SELECT 查询，内嵌分区裁剪检查与成本熔断限制。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "待执行的 SELECT SQL 语句（只读，分区表必须指定分区过滤条件）",
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": "最大返回行数，默认 100，最高 1000",
                    },
                },
                "required": ["sql"],
            },
        },
    },
]

TOOL_MAP = {
    "search_semantic_catalog": search_semantic_catalog,
    "get_dimension_values": get_dimension_values,
    "list_tables": list_tables,
    "describe_table": describe_table,
    "execute_sql": execute_sql,
}

SYSTEM_PROMPT = """你是一个顶级的企业级 MaxCompute 数据分析专家。
你的职责是帮助企业员工通过自然语言准确、高效、安全地分析业务数据。

### 【文风规范（Strict Report Style）】
- 严禁 AI 废话套话：禁止使用“一句话总结：”、“总的来说”、“不是……而是……”、“值得注意的是”等修饰填充词。
- 开门见山：禁止前言寒暄客套，直接陈述数据事实、表格与量化差距。
- 简明报告：输出简明高管简报，数据严谨，杜绝空话。

### 【工具调度 SOP 工作流（必须严格遵循）】
当用户提出业务问数需求时，严格按以下 4 步执行：
1. 【语义对齐】：遇到具体业务指标或维度，优先调用 search_semantic_catalog 检索标准计算公式、底层物理表及默认过滤条件。涉及枚举疑问时，调用 get_dimension_values。若需探索全局表名，调用 list_tables。
2. 【分区感知】：若涉及分区表，必须先调用 describe_table 查询该表最新已产出的分区（如 pt 或 ds）。严格禁止编写不带分区条件的查询，杜绝全表扫描。
3. 【SQL 编写与安全执行】：编写只读 SELECT 语句，在 WHERE 条件中包含分区条件与 default_filter，调用 execute_sql。系统会自动注入 LIMIT 100。
4. 【结构化交付】：直接给出核心指标与 Markdown 表格，并标注口径依据与数据表来源。
"""

# ------------------------------------------------------------------------------
# 3. Agent Execution Engine
# ------------------------------------------------------------------------------
def call_qwen(messages: list[dict]) -> dict:
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {BAILIAN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.1,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Bailian API error: {resp.status_code} - {resp.text}")
    return resp.json()["choices"][0]["message"]


def run_agent_loop(user_input: str) -> None:
    print(f"\n👤 用户提问: {user_input}")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    max_steps = 8
    step = 0
    while step < max_steps:
        step += 1
        msg = call_qwen(messages)
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            # Final text response
            print(f"\n🤖 千问 Data Agent 回答:\n{msg.get('content')}\n")
            break

        # Execute tools
        for tc in tool_calls:
            fn = tc.get("function", {})
            fn_name = fn.get("name")
            try:
                fn_args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                fn_args = {}

            print(f"\n⚙️ [Step {step}] 千问正在调用工具: \033[1;34m{fn_name}\033[0m")
            print(f"   参数: {json.dumps(fn_args, ensure_ascii=False)}")

            tool_fn = TOOL_MAP.get(fn_name)
            if tool_fn:
                try:
                    result = tool_fn(**fn_args)
                except Exception as e:
                    result = {"error": str(e)}
            else:
                result = {"error": f"Tool '{fn_name}' not implemented"}

            # Print brief preview of result
            result_str = json.dumps(result, ensure_ascii=False)
            preview = result_str[:160] + "..." if len(result_str) > 160 else result_str
            print(f"   返回: \033[1;32m{preview}\033[0m")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": result_str,
            })


def main() -> None:
    print("=" * 70)
    print("  🚀 千问 MaxCompute Data Agent 本地测试环境")
    print(f"  🧠 模型: {MODEL_NAME}")
    print("=" * 70)

    if len(sys.argv) > 1:
        # One-shot query mode
        query = " ".join(sys.argv[1:])
        run_agent_loop(query)
    else:
        # Interactive REPL mode
        print("\n请输入你的数据业务问题（输入 'exit' 或 'q' 退出）：")
        while True:
            try:
                query = input("\n💬 > ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "q", "quit"]:
                    print("👋 再见！")
                    break
                run_agent_loop(query)
            except KeyboardInterrupt:
                print("\n👋 退出。")
                break


if __name__ == "__main__":
    main()
