"""Inject controlled, documented data-quality issues into synthetic raw landing data.

The generator first creates and validates coherent business entities and relationships.
This optional raw-source layer then introduces a small number of realistic ingestion
issues for Power Query/Silver-layer practice without changing keys, foreign keys, or
row counts. All records remain synthetic.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def inject_raw_quality_issues(generator: Any, rate: float = 0.025) -> dict[str, Any]:
    """Inject safe, reproducible raw-data defects while preserving relationship keys."""
    if not 0 < rate <= 0.10:
        raise ValueError("rate must be greater than 0 and at most 0.10")

    rng = random.Random(generator.seed + 913_721)
    datasets = generator.datasets
    issues: dict[str, int] = {
        "optional_text_nulls": 0,
        "text_whitespace_variants": 0,
        "timestamp_format_variants": 0,
    }
    protected_fk_columns = {(table, col) for (table, col) in generator.references}
    nullable_text_targets = (
        ("profiles", "bio"),
        ("profiles", "website"),
        ("statuses", "caption"),
        ("comments", "reply"),
        ("collections", "description"),
    )
    for table_name, column_name in nullable_text_targets:
        table = generator.schema.tables.get(table_name)
        rows = datasets.get(table_name, [])
        if not table or column_name not in table.column_names:
            continue
        column = table.col(column_name)
        if not column.nullable or column.primary_key or column.unique:
            continue
        if (table_name, column_name) in protected_fk_columns:
            continue
        eligible = [row for row in rows if isinstance(row.get(column_name), str) and row[column_name].strip()]
        count = min(len(eligible), max(1, round(len(eligible) * rate))) if eligible else 0
        for row in rng.sample(eligible, count):
            row[column_name] = None
            issues["optional_text_nulls"] += 1

    for table_name, column_name in (("statuses", "caption"), ("profiles", "bio"), ("comments", "reply")):
        rows = datasets.get(table_name, [])
        eligible = [row for row in rows if isinstance(row.get(column_name), str) and row[column_name].strip()]
        count = min(len(eligible), max(1, round(len(eligible) * rate))) if eligible else 0
        for row in rng.sample(eligible, count):
            row[column_name] = f"  {row[column_name].strip()}  "
            issues["text_whitespace_variants"] += 1

    status_rows = datasets.get("statuses", [])
    eligible_dates = [row for row in status_rows if _parse_datetime(row.get("created_at")) is not None]
    count = min(len(eligible_dates), max(1, round(len(eligible_dates) * rate))) if eligible_dates else 0
    for row in rng.sample(eligible_dates, count):
        parsed = _parse_datetime(row["created_at"])
        if parsed is not None:
            row["created_at"] = parsed.strftime("%Y/%m/%d %H:%M:%S")
            issues["timestamp_format_variants"] += 1

    return {
        "enabled": True,
        "profile": "controlled_raw_source_issues_v1",
        "synthetic_only": True,
        "rate": rate,
        "row_count_changed": False,
        "primary_keys_changed": False,
        "foreign_keys_changed": False,
        "business_relationships_rewritten": False,
        "issues": issues,
        "total_injected_issues": sum(issues.values()),
        "silver_layer_exercises": [
            "profile and caption NULL handling",
            "free-text trimming",
            "mixed timestamp format normalization",
        ],
        "warning": (
            "These are intentional Bronze/landing defects. Do not treat the raw files as "
            "cleaned analytics tables; document and resolve them in staging/Silver."
        ),
    }
