"""Semantic Engine for MaxCompute Data Agent.

Parses and indexes semantic_layer.yaml to provide fast, token-efficient
business metric & dimension search for LLM Data Agents.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import yaml

DEFAULT_YAML_PATH = Path(__file__).parent / "semantic_layer.yaml"


class SemanticEngine:
    def __init__(self, yaml_path: Path | str | None = None) -> None:
        self.yaml_path = Path(yaml_path or DEFAULT_YAML_PATH)
        self.raw_data: dict[str, Any] = {}
        self.dimensions: dict[str, dict[str, Any]] = {}
        self.models: dict[str, dict[str, Any]] = {}
        self.composite_metrics: dict[str, dict[str, Any]] = {}
        self.table_to_model: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Semantic layer definition not found at: {self.yaml_path}")
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            self.raw_data = yaml.safe_load(f) or {}

        # 1. Index dimensions
        for dim in self.raw_data.get("dimensions", []):
            name = dim.get("name")
            if name:
                self.dimensions[name] = dim
                src_tbl = dim.get("source_table")
                if src_tbl:
                    self.table_to_model[src_tbl] = name

        # 2. Index semantic models
        self.table_default_filters: dict[str, str] = {}
        for model in self.raw_data.get("semantic_models", []):
            name = model.get("name")
            if name:
                self.models[name] = model
                src_tbl = model.get("source_table")
                if src_tbl:
                    self.table_to_model[src_tbl] = name
                    d_filter = model.get("default_filter")
                    if d_filter:
                        self.table_default_filters[src_tbl.lower()] = d_filter

        # 3. Index composite metrics
        for cm in self.raw_data.get("composite_metrics", []):
            name = cm.get("name")
            if name:
                self.composite_metrics[name] = cm

    def search(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Search metrics, models, and dimensions using business query terms.

        Matches against names, labels, descriptions, and synonyms.
        """
        query_str = (query or "").strip().lower()
        if not query_str:
            return {
                "matched_metrics": [],
                "matched_models": [],
                "matched_dimensions": [],
            }

        # Tokenize query by space and punctuation
        raw_tokens = [t.strip() for t in query_str.replace(",", " ").replace("，", " ").split() if t.strip()]
        if query_str not in raw_tokens:
            tokens = [query_str] + raw_tokens
        else:
            tokens = raw_tokens

        matched_metrics: list[tuple[int, dict[str, Any]]] = []
        matched_models: list[tuple[int, dict[str, Any]]] = []
        matched_dimensions: list[tuple[int, dict[str, Any]]] = []

        def calc_score(targets: list[str]) -> int:
            score = 0
            for t in targets:
                t_low = str(t).lower()
                for token in tokens:
                    if token == t_low:
                        score += 10
                    elif token in t_low:
                        score += 5
                    elif t_low in token:
                        score += 3
            return score

        # 1. Search composite metrics
        for name, cm in self.composite_metrics.items():
            targets = [name, cm.get("label", ""), cm.get("description", "")] + list(cm.get("synonyms", []))
            score = calc_score(targets)
            if score > 0:
                matched_metrics.append((score, {
                    "metric_name": name,
                    "type": "composite_metric",
                    "label": cm.get("label"),
                    "description": cm.get("description"),
                    "formula": cm.get("sql") or f"{cm.get('numerator')} / {cm.get('denominator')}",
                    "format": cm.get("format"),
                }))

        # 2. Search semantic models & measures
        for model_name, model in self.models.items():
            model_targets = [model_name, model.get("label", ""), model.get("description", ""), model.get("source_table", "")]
            m_score = calc_score(model_targets)
            if m_score > 0:
                matched_models.append((m_score, {
                    "model_name": model_name,
                    "label": model.get("label"),
                    "source_table": model.get("source_table"),
                    "default_filter": model.get("default_filter"),
                    "joins": model.get("joins", []),
                }))

            # Search measures in model
            for measure in model.get("measures", []):
                meas_targets = [
                    measure.get("name", ""),
                    measure.get("label", ""),
                    measure.get("description", "")
                ] + list(measure.get("synonyms", []))
                meas_score = calc_score(meas_targets)
                if meas_score > 0:
                    matched_metrics.append((meas_score, {
                        "metric_name": measure.get("name"),
                        "type": "model_measure",
                        "label": measure.get("label"),
                        "model": model_name,
                        "source_table": model.get("source_table"),
                        "aggregation": measure.get("type"),
                        "sql_expression": measure.get("sql"),
                        "default_filter": model.get("default_filter"),
                        "recommended_joins": model.get("joins", []),
                        "format": measure.get("format"),
                    }))

        # 3. Search dimensions & fields
        for dim_name, dim in self.dimensions.items():
            dim_targets = [dim_name, dim.get("label", ""), dim.get("description", ""), dim.get("source_table", "")]
            d_score = calc_score(dim_targets)
            
            matched_fields = []
            for field in dim.get("fields", []):
                f_targets = [
                    field.get("name", ""),
                    field.get("label", ""),
                    field.get("description", "")
                ] + list(field.get("synonyms", []))
                f_score = calc_score(f_targets)
                if f_score > 0:
                    d_score += f_score
                    matched_fields.append({
                        "field_name": field.get("name"),
                        "label": field.get("label"),
                        "type": field.get("type"),
                        "allowed_values": field.get("allowed_values"),
                    })

            if d_score > 0:
                matched_dimensions.append((d_score, {
                    "dimension_name": dim_name,
                    "label": dim.get("label"),
                    "source_table": dim.get("source_table"),
                    "primary_key": dim.get("primary_key"),
                    "matched_fields": matched_fields[:5],
                }))

        # Sort and take top_k
        matched_metrics.sort(key=lambda x: x[0], reverse=True)
        matched_models.sort(key=lambda x: x[0], reverse=True)
        matched_dimensions.sort(key=lambda x: x[0], reverse=True)

        return {
            "query": query,
            "matched_metrics": [m[1] for m in matched_metrics[:top_k]],
            "matched_models": [m[1] for m in matched_models[:top_k]],
            "matched_dimensions": [d[1] for d in matched_dimensions[:top_k]],
        }

    def get_dimension_values(self, dimension_name: str, field_name: str) -> dict[str, Any]:
        """Get allowed values and definition for a specific dimension field."""
        dim = self.dimensions.get(dimension_name)
        if not dim:
            # Try fuzzy match
            for d in self.dimensions.values():
                if dimension_name.lower() in d.get("name", "").lower() or dimension_name.lower() in d.get("label", "").lower():
                    dim = d
                    break

        if not dim:
            return {"error": f"Dimension '{dimension_name}' not found."}

        for field in dim.get("fields", []):
            if field.get("name", "").lower() == field_name.lower() or field_name.lower() in [s.lower() for s in field.get("synonyms", [])]:
                return {
                    "dimension": dim.get("name"),
                    "source_table": dim.get("source_table"),
                    "field_name": field.get("name"),
                    "label": field.get("label"),
                    "type": field.get("type"),
                    "allowed_values": field.get("allowed_values", []),
                    "description": field.get("description"),
                }

        return {"error": f"Field '{field_name}' not found in dimension '{dim.get('name')}'."}


# Global singleton instance
_engine_instance: SemanticEngine | None = None


def get_semantic_engine() -> SemanticEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SemanticEngine()
    return _engine_instance
