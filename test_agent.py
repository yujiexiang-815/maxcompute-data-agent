"""Automated End-to-End Tests for MaxCompute Data Agent.

Validates semantic catalog search, metadata introspection, guardrail enforcement,
and safe SQL execution.
"""

from __future__ import annotations

import unittest
from uuid import uuid4
from starlette.testclient import TestClient

from server import (
    search_semantic_catalog,
    get_dimension_values,
    get_table_metadata,
    execute_safe_sql,
    create_sse_app,
)


class TestDataAgent(unittest.TestCase):

    def test_01_search_semantic_catalog_gmv(self):
        """Test searching for GMV / 销售额 returns relevant retail metrics."""
        result = search_semantic_catalog("销售额", top_k=3)
        self.assertIn("matched_metrics", result)
        self.assertGreater(len(result["matched_metrics"]), 0)
        labels = [m.get("label") for m in result["matched_metrics"]]
        print("\n[Test 1] Matched GMV metrics:", labels)
        self.assertTrue(any("销售" in str(l) or "GMV" in str(l) for l in labels))

    def test_02_search_semantic_catalog_achievement_rate(self):
        """Test searching composite metric '达成率'."""
        result = search_semantic_catalog("达成率", top_k=3)
        self.assertIn("matched_metrics", result)
        metric_names = [m.get("metric_name") for m in result["matched_metrics"]]
        print("[Test 2] Matched Rate metrics:", metric_names)
        self.assertIn("target_achievement_rate", metric_names)

    def test_03_get_dimension_values(self):
        """Test retrieving allowed values for store channel."""
        result = get_dimension_values("dim_store", "channel")
        print("[Test 3] Dimension values:", result)
        self.assertEqual(result.get("field_name"), "channel")
        self.assertIn("DTC", result.get("allowed_values", []))
        self.assertIn("B2B", result.get("allowed_values", []))

    def test_04_get_table_metadata_unpartitioned(self):
        """Test metadata retrieval for dws_fact_retail_sales_order."""
        meta = get_table_metadata("dws_fact_retail_sales_order")
        print("[Test 4] Metadata columns count:", len(meta.get("columns", [])))
        self.assertFalse(meta.get("is_partitioned"))
        self.assertGreater(len(meta.get("columns", [])), 0)

    def test_05_get_table_metadata_partitioned(self):
        """Test metadata retrieval for partitioned table dwd_inventory_channel_day."""
        meta = get_table_metadata("dwd_inventory_channel_day")
        print("[Test 5] Partitioned table recent partitions:", meta.get("recent_partitions"))
        self.assertTrue(meta.get("is_partitioned"))
        self.assertGreater(len(meta.get("recent_partitions", [])), 0)

    def test_06_guardrail_blocks_ddl(self):
        """Test that DDL/DML statements like DROP are blocked."""
        res = execute_safe_sql("DROP TABLE dws_fact_retail_sales_order")
        print("[Test 6] DROP Table response:", res)
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "GuardrailViolation")

    def test_07_guardrail_blocks_unpartitioned_query(self):
        """Test that querying a partitioned table without partition condition is blocked."""
        res = execute_safe_sql("SELECT * FROM dwd_inventory_channel_day")
        print("[Test 7] Unpartitioned query response:", res.get("message"))
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "GuardrailViolation")
        self.assertIn("成本护栏拦截", res.get("message", ""))

    def test_08_safe_sql_execution(self):
        """Test executing a safe SELECT query with LIMIT auto-injection."""
        res = execute_safe_sql("SELECT store_code, channel FROM mdm_dim_store_info", max_rows=5)
        print("[Test 8] Executed SQL:", res.get("executed_sql"))
        print("[Test 8] Row count:", res.get("row_count"))
        self.assertTrue(res.get("success"))
        self.assertIn("LIMIT 5", res.get("executed_sql", ""))
        self.assertLessEqual(res.get("row_count", 0), 5)

    def test_09_guardrail_blocks_missing_semantic_filter(self):
        """Test that querying dws_fact_retail_sales_order without is_valid_data is blocked."""
        res = execute_safe_sql("SELECT store_code, sum(total_paid) FROM dws_fact_retail_sales_order GROUP BY store_code")
        print("[Test 9] Missing semantic filter response:", res.get("message"))
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "GuardrailViolation")
        self.assertIn("语义护栏拦截", res.get("message", ""))

    def test_10_sse_app_endpoints(self):
        """Test SSE server endpoints: GET /health, POST /sse guidance, and GET /sse route existence."""
        app = create_sse_app(host="127.0.0.1")
        client = TestClient(app, base_url="http://127.0.0.1:8000")

        # 1. GET /health should succeed with HTTP 200
        health_resp = client.get("/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.json().get("status"), "ok")
        print("[Test 10] Health check OK:", health_resp.json())

        # 2. POST /sse should return 405 Method Not Allowed with helpful hint
        post_sse_resp = client.post("/sse")
        self.assertEqual(post_sse_resp.status_code, 405)
        self.assertIn("The /sse endpoint only accepts HTTP GET", post_sse_resp.json().get("message", ""))
        print("[Test 10] POST /sse guidance OK:", post_sse_resp.json().get("message"))

    def test_11_smart_session_fallback(self):
        """Test that stale/expired session IDs are transparently re-routed to active SSE session."""
        from mcp.server.sse import SseServerTransport

        app = create_sse_app(host="127.0.0.1")
        client = TestClient(app, base_url="http://127.0.0.1:8000")

        # Find transport
        transport = None
        for r in app.routes:
            if hasattr(r, "app") and hasattr(r.app, "__self__"):
                if isinstance(r.app.__self__, SseServerTransport):
                    transport = r.app.__self__
                    break

        self.assertIsNotNone(transport)

        # Mock an active session
        active_id = uuid4()
        class MockWriter:
            async def send(self, msg):
                pass
        transport._read_stream_writers[active_id] = MockWriter()

        # Check health reflects active sessions
        health_resp = client.get("/health")
        self.assertEqual(health_resp.json().get("active_sessions"), 1)

        # POST with a stale/dead session ID
        dead_session_id = uuid4().hex
        post_resp = client.post(
            f"/messages/?session_id={dead_session_id}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
        )
        # Should NOT return 404 "Could not find session"; it accepts (202) because of fallback
        self.assertEqual(post_resp.status_code, 202)
        print("[Test 11] Stale session fallback passed: 202 Accepted instead of 404")


if __name__ == "__main__":
    unittest.main(verbosity=2)
