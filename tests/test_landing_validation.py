"""Tests for landing zone validation logic and manifest contracts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest


def test_landing_manifest_contract_if_present(project_root: Path):
    """If local landing directory exists, verify manifest schema contracts."""
    landing_dir = project_root / "data" / "landing"
    manifest_file = landing_dir / "metadata" / "manifest.json"

    if not manifest_file.exists():
        pytest.skip("Landing zone not generated yet; skipping local manifest validation")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["schema_table_count"] == 54
    assert manifest["unique_physical_representation_per_table"] is True
    assert sum(manifest["format_table_counts"].values()) == 54


def test_sqlite_integrity_if_present(project_root: Path):
    """If local SQLite operational database exists, check SQLite integrity pragmas."""
    db_file = project_root / "data" / "landing" / "sqlite" / "pixelfed_operational_tables.sqlite"

    if not db_file.exists():
        pytest.skip("SQLite database not found in landing; skipping integrity check")

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]
        assert integrity == "ok", f"SQLite integrity_check failed: {integrity}"

        fk_violations = cursor.execute("PRAGMA foreign_key_check").fetchall()
        assert len(fk_violations) == 0, f"SQLite foreign-key check violations: {fk_violations}"
