"""Tests for Lakehouse mixed-format assignment contracts."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from schema_generator_core import SchemaContract
from generate_landing import FORMAT_GROUPS


def test_format_group_counts():
    """Verify exact table count per format group in the lakehouse contract."""
    expected_counts = {
        "csv_gz": 11,
        "csv": 10,
        "jsonl": 8,
        "json": 5,
        "xlsx": 7,
        "sqlite": 13,
    }
    actual_counts = {fmt: len(tables) for fmt, tables in FORMAT_GROUPS.items()}
    assert actual_counts == expected_counts, f"Format count mismatch: {actual_counts} != {expected_counts}"
    assert sum(actual_counts.values()) == 54, f"Total format allocations must equal 54, got {sum(actual_counts.values())}"


def test_no_overlapping_table_assignments():
    """Ensure no table is duplicated or assigned to multiple physical formats."""
    seen = set()
    duplicates = []
    for fmt, tables in FORMAT_GROUPS.items():
        for table in tables:
            if table in seen:
                duplicates.append(table)
            seen.add(table)
    assert not duplicates, f"Found tables assigned to multiple formats: {duplicates}"
    assert len(seen) == 54


def test_all_schema_tables_covered(parsed_schema: SchemaContract, format_assignment: dict[str, str]):
    """Every table in schema.md must have an assigned format."""
    schema_tables = set(parsed_schema.tables.keys())
    assigned_tables = set(format_assignment.keys())
    assert schema_tables == assigned_tables, (
        f"Missing: {schema_tables - assigned_tables}, Unexpected: {assigned_tables - schema_tables}"
    )


def test_config_json_matches_python_definition(project_root: Path):
    """Verify config/table_format_assignment.json matches python FORMAT_GROUPS."""
    config_file = project_root / "config" / "table_format_assignment.json"
    if not config_file.exists():
        config_file = project_root / "config_table_format_assignment.json"
    assert config_file.is_file(), "Table format assignment config JSON not found"

    config_data = json.loads(config_file.read_text(encoding="utf-8"))
    for fmt, tables in FORMAT_GROUPS.items():
        assert sorted(config_data["formats"][fmt]) == sorted(tables), f"Mismatch in {fmt} assignment"
