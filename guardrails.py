"""MaxCompute Cost and Security Guardrails.

Provides AST/regex-based security checks, partition pruning enforcement,
and automatic LIMIT injection to prevent high scan costs and injection attacks.
"""

from __future__ import annotations

import re
from typing import Any

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "TRUNCATE",
    "CREATE", "ALTER", "RENAME", "OVERWRITE", "MSCK", "RECOVER",
    "GRANT", "REVOKE", "SET ROLE", "ADD", "REMOVE", "LOAD",
    "UNLOAD", "EXPORT", "IMPORT", "TUNNEL", "KILL", "PURGE"
]

# Common partition column patterns in MaxCompute
PARTITION_COL_PATTERNS = [r"\bds\b", r"\bpt\b", r"\bdt\b", r"\bpartition\b"]


class GuardrailViolation(ValueError):
    """Raised when a query violates safety or cost guardrails."""
    pass


class MaxComputeGuardrail:
    def __init__(self, default_limit: int = 100, max_limit: int = 1000) -> None:
        self.default_limit = default_limit
        self.max_limit = max_limit

    def sanitize_sql(self, sql: str) -> str:
        """Strip comments and normalize spaces."""
        # Strip single line comments -- ...
        cleaned = re.sub(r"--[^\n]*", "", sql)
        # Strip multi-line comments /* ... */
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def validate_single_statement(self, sql: str) -> None:
        """Ensure no chained queries with semicolons."""
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        if len(statements) > 1:
            raise GuardrailViolation(
                "Multiple statements detected. Only a single SELECT/SHOW statement is allowed."
            )

    def validate_read_only(self, sql: str) -> None:
        """Enforce read-only semantics."""
        cleaned = self.sanitize_sql(sql)
        upper_sql = cleaned.upper()

        # Must start with SELECT, WITH, SHOW, DESC, DESCRIBE
        first_token = upper_sql.split()[0] if upper_sql.split() else ""
        allowed_starts = ["SELECT", "WITH", "SHOW", "DESC", "DESCRIBE"]
        if first_token not in allowed_starts:
            raise GuardrailViolation(
                f"Prohibited statement type. Queries must begin with one of {allowed_starts}, got '{first_token}'."
            )

        # Check for forbidden mutation keywords
        # Use regex word boundaries to avoid false positives (e.g., 'created_at' matching 'CREATE')
        for kw in FORBIDDEN_KEYWORDS:
            pattern = rf"\b{kw}\b"
            if re.search(pattern, upper_sql):
                raise GuardrailViolation(
                    f"Prohibited operation: '{kw}' keyword is not permitted in read-only mode."
                )

    def validate_partition_pruning(self, sql: str, partitioned_tables: list[str]) -> None:
        """Enforce partition filtering for partitioned tables.

        Args:
            sql: The cleaned SQL query.
            partitioned_tables: List of partitioned table names referenced or known.
        """
        if not partitioned_tables:
            return

        cleaned = self.sanitize_sql(sql)
        upper_sql = cleaned.upper()

        for table in partitioned_tables:
            tbl_upper = table.upper()
            # Check if this table is referenced in FROM or JOIN
            table_ref_pattern = rf"\b(FROM|JOIN)\s+([a-zA-Z0-9_\.]*\.)?{tbl_upper}\b"
            if re.search(table_ref_pattern, upper_sql):
                # Check if WHERE clause contains partition columns (ds, pt, etc.)
                has_partition_filter = any(
                    re.search(pat, cleaned, flags=re.IGNORECASE) for pat in PARTITION_COL_PATTERNS
                )
                if not has_partition_filter:
                    raise GuardrailViolation(
                        f"MaxCompute 成本护栏拦截: 数据表 '{table}' 为分区表。"
                        f"为防止全表扫描产生高额计费，必须在 WHERE 子句中显式指定分区过滤条件（如 `ds = 'YYYYMMDD'` 或 `ds >= '...'`）。"
                        f"建议先调用 `get_table_metadata` 获取该表的最新可用分区。"
                    )

    def validate_semantic_filters(self, sql: str, table_default_filters: dict[str, str]) -> None:
        """Enforce default filters from semantic layer (e.g. is_valid_data = 1)."""
        if not table_default_filters:
            return

        cleaned = self.sanitize_sql(sql)
        upper_sql = cleaned.upper()

        for table, d_filter in table_default_filters.items():
            tbl_upper = table.upper()
            table_ref_pattern = rf"\b(FROM|JOIN)\s+([a-zA-Z0-9_\.]*\.)?{tbl_upper}\b"
            if re.search(table_ref_pattern, upper_sql):
                # Check for the key column name in the filter (e.g. 'is_valid_data' in 'is_valid_data = 1')
                key_col = d_filter.split("=")[0].strip().split()[0].upper()
                if not re.search(rf"\b{key_col}\b", upper_sql):
                    raise GuardrailViolation(
                        f"MaxCompute 语义护栏拦截: 数据表 '{table}' 必须遵循业务语义口径，"
                        f"显式包含默认过滤条件 `{d_filter}`。"
                        f"建议先调用 `search_semantic_catalog` 对齐指标口径与过滤规则。"
                    )

    def enforce_limit(self, sql: str, requested_limit: int | None = None) -> tuple[str, int]:
        """Inject or clamp LIMIT to prevent overwhelming results and high data export costs.

        Returns:
            (rewritten_sql, effective_limit)
        """
        cleaned = self.sanitize_sql(sql).rstrip(";")
        limit_to_use = min(requested_limit or self.default_limit, self.max_limit)

        # Check if query already has LIMIT
        match = re.search(r"\bLIMIT\s+(\d+)\b", cleaned, flags=re.IGNORECASE)
        if match:
            existing_limit = int(match.group(1))
            if existing_limit > self.max_limit:
                # Replace with max_limit
                rewritten_sql = re.sub(
                    r"\bLIMIT\s+\d+\b",
                    f"LIMIT {self.max_limit}",
                    cleaned,
                    flags=re.IGNORECASE
                )
                return rewritten_sql, self.max_limit
            return cleaned, min(existing_limit, self.max_limit)
        else:
            # Append LIMIT
            # If statement starts with SHOW or DESC, LIMIT is usually not required or applicable
            first_word = cleaned.split()[0].upper() if cleaned.split() else ""
            if first_word in ["SHOW", "DESC", "DESCRIBE"]:
                return cleaned, limit_to_use
            rewritten_sql = f"{cleaned} LIMIT {limit_to_use}"
            return rewritten_sql, limit_to_use

    def verify_and_prepare_sql(
        self,
        sql: str,
        max_rows: int = 100,
        partitioned_tables: list[str] | None = None,
        table_default_filters: dict[str, str] | None = None
    ) -> tuple[str, int]:
        """Complete verification and rewrite pipeline."""
        self.validate_single_statement(sql)
        self.validate_read_only(sql)
        if partitioned_tables:
            self.validate_partition_pruning(sql, partitioned_tables)
        if table_default_filters:
            self.validate_semantic_filters(sql, table_default_filters)
        return self.enforce_limit(sql, max_rows)
