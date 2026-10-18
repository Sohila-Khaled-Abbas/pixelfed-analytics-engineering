#!/usr/bin/env python3
"""Validate the mixed-format landing zone against its manifest and schema contract."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sqlite3
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]

from generate_landing import build_table_format_map  # noqa: E402
from schema_generator_core import parse_schema  # noqa: E402


def quote_identifier(identifier: str) -> str:
    """Safely quote a SQLite identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def read_row_counts(path: Path, errors: list[str]) -> dict[str, int]:
    """Read row counts and report duplicate, malformed, or missing metadata."""
    if not path.is_file():
        errors.append(f"Missing row-count metadata: {path}")
        return {}

    counts: dict[str, int] = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            table_name = row.get("table_name", "").strip()
            try:
                count = int(row["row_count"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"Invalid row-count metadata row: {row}")
                continue

            if not table_name:
                errors.append(f"Row-count metadata has an empty table name: {row}")
            elif table_name in counts:
                errors.append(f"Duplicate row-count metadata for table: {table_name}")
            else:
                counts[table_name] = count

    return counts


def validate_landing(landing: Path, schema_path: Path) -> int:
    """Validate assigned files, table schemas, row counts, and SQLite integrity."""
    errors: list[str] = []
    schema = parse_schema(schema_path)
    expected_formats = build_table_format_map(schema)

    manifest_path = landing / "metadata" / "manifest.json"
    if not manifest_path.is_file():
        print(f"VALIDATION FAILED\n- Missing manifest: {manifest_path}")
        return 1

    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"VALIDATION FAILED\n- Could not read manifest: {exc}")
        return 1

    table_storage = manifest.get("table_storage", {})
    if not isinstance(table_storage, dict):
        print("VALIDATION FAILED\n- Manifest table_storage must be an object")
        return 1

    if set(table_storage) != set(schema.tables):
        errors.append("Manifest table set does not match schema")
    actual_formats = {
        table_name: info.get("format") for table_name, info in table_storage.items() if isinstance(info, dict)
    }
    if actual_formats != expected_formats:
        errors.append("Table-format assignment mismatch")
    if manifest.get("schema_table_count") != len(schema.tables):
        errors.append(f"Manifest schema_table_count {manifest.get('schema_table_count')} != {len(schema.tables)}")
    if manifest.get("unique_physical_representation_per_table") is not True:
        errors.append("Manifest does not assert unique physical representation per table")

    row_counts = read_row_counts(landing / "metadata" / "row_counts.csv", errors)
    if set(row_counts) != set(schema.tables):
        errors.append("Row-count metadata table set does not match schema")

    expected_sqlite_tables = {name for name, fmt in expected_formats.items() if fmt == "sqlite"}
    sqlite_tables: set[str] = set()
    db_path = landing / "sqlite" / "pixelfed_operational_tables.sqlite"
    if not db_path.is_file():
        errors.append(f"Missing SQLite database: {db_path}")
    else:
        try:
            with sqlite3.connect(db_path) as connection:
                sqlite_tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                    )
                }
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    errors.append(f"SQLite integrity_check failed: {integrity}")
                foreign_key_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
                if foreign_key_violations:
                    errors.append(f"SQLite foreign-key violations: {len(foreign_key_violations)}")
        except sqlite3.Error as exc:
            errors.append(f"Could not validate SQLite database: {exc}")

        if sqlite_tables != expected_sqlite_tables:
            missing = sorted(expected_sqlite_tables - sqlite_tables)
            extra = sorted(sqlite_tables - expected_sqlite_tables)
            errors.append(f"SQLite table set mismatch; missing={missing}, extra={extra}")

    observed_rows = 0
    for table_name, file_format in expected_formats.items():
        table_spec = schema.tables[table_name]
        info = table_storage.get(table_name, {})
        if not isinstance(info, dict):
            errors.append(f"{table_name}: missing or invalid manifest entry")
            continue

        physical_file = info.get("file")
        if not isinstance(physical_file, str) or not physical_file:
            errors.append(f"{table_name}: missing physical file path in manifest")
            continue

        expected_path = (
            "sqlite/pixelfed_operational_tables.sqlite"
            if file_format == "sqlite"
            else f"{file_format}/{table_name}."
            + {
                "csv": "csv",
                "csv_gz": "csv.gz",
                "jsonl": "jsonl",
                "json": "json",
                "xlsx": "xlsx",
            }[file_format]
        )
        if physical_file != expected_path:
            errors.append(f"{table_name}: manifest path {physical_file!r} != assigned path {expected_path!r}")

        row_count = 0
        try:
            if file_format in {"csv", "csv_gz"}:
                path = landing / physical_file
                opener = gzip.open if file_format == "csv_gz" else open
                with opener(path, "rt", encoding="utf-8", newline="") as stream:
                    reader = csv.reader(stream)
                    header = next(reader)
                    row_count = sum(1 for _ in reader)
                if header != table_spec.column_names:
                    errors.append(f"{table_name}: CSV header/column order differs from schema")

            elif file_format in {"json", "jsonl"}:
                path = landing / physical_file
                if file_format == "json":
                    records = json.loads(path.read_text(encoding="utf-8"))
                else:
                    with path.open(encoding="utf-8") as stream:
                        records = [json.loads(line) for line in stream if line.strip()]
                if not isinstance(records, list):
                    errors.append(f"{table_name}: expected a JSON array or JSONL records")
                    records = []
                row_count = len(records)
                if records and (not isinstance(records[0], dict) or list(records[0]) != table_spec.column_names):
                    errors.append(f"{table_name}: JSON column order/name mismatch")

            elif file_format == "xlsx":
                workbook = load_workbook(
                    landing / physical_file,
                    read_only=True,
                    data_only=True,
                )
                try:
                    sheet_name = table_name[:31]
                    if sheet_name not in workbook.sheetnames:
                        errors.append(f"{table_name}: missing XLSX worksheet {sheet_name!r}")
                        continue
                    worksheet = workbook[sheet_name]
                    values = worksheet.iter_rows(values_only=True)
                    header = list(next(values))
                    if header != table_spec.column_names:
                        errors.append(f"{table_name}: XLSX column order/name mismatch")
                    row_count = sum(1 for _ in values)
                finally:
                    workbook.close()

            elif file_format == "sqlite":
                if not db_path.is_file() or table_name not in sqlite_tables:
                    continue
                quoted_table = quote_identifier(table_name)
                with sqlite3.connect(db_path) as connection:
                    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({quoted_table})")]
                    row_count = connection.execute(f"SELECT COUNT(*) FROM {quoted_table}").fetchone()[0]
                if columns != table_spec.column_names:
                    errors.append(f"{table_name}: SQLite column order/name mismatch")

            if table_name in row_counts and row_count != row_counts[table_name]:
                errors.append(f"{table_name}: row count {row_count} != expected {row_counts[table_name]}")
            observed_rows += row_count
        except (
            OSError,
            csv.Error,
            gzip.BadGzipFile,
            json.JSONDecodeError,
            StopIteration,
            sqlite3.Error,
            ValueError,
        ) as exc:
            errors.append(f"{table_name}: read/validation error: {exc}")

    # Detect duplicate, unexpected, or misplaced non-SQLite files.
    allowed_extensions = {
        "csv": ".csv",
        "csv_gz": ".csv.gz",
        "json": ".json",
        "jsonl": ".jsonl",
        "xlsx": ".xlsx",
    }
    seen_physical: dict[str, str] = {}
    for folder, extension in allowed_extensions.items():
        folder_path = landing / folder
        if not folder_path.exists():
            continue
        for file_path in folder_path.glob(f"*{extension}"):
            table_name = file_path.name[: -len(extension)]
            relative_path = f"{folder}/{file_path.name}"
            if table_name in seen_physical:
                errors.append(f"Duplicate table file {table_name}: {seen_physical[table_name]} and {relative_path}")
            else:
                seen_physical[table_name] = relative_path

    expected_file_tables = {name for name, fmt in expected_formats.items() if fmt != "sqlite"}
    if set(seen_physical) != expected_file_tables:
        missing = sorted(expected_file_tables - set(seen_physical))
        extra = sorted(set(seen_physical) - expected_file_tables)
        errors.append(f"Physical file set mismatch; missing={missing}, extra={extra}")

    for table_name, file_format in expected_formats.items():
        if file_format == "sqlite":
            continue
        expected_path = table_storage.get(table_name, {}).get("file")
        if expected_path and seen_physical.get(table_name) != expected_path:
            errors.append(
                f"{table_name}: physical file is {seen_physical.get(table_name)!r}, expected {expected_path!r}"
            )

    total_rows = manifest.get("total_rows")
    if observed_rows != total_rows:
        errors.append(f"Total row mismatch: {observed_rows} != {total_rows}")
    if row_counts and sum(row_counts.values()) != total_rows:
        errors.append(f"Row-count metadata total {sum(row_counts.values())} != manifest total {total_rows}")

    if errors:
        print("VALIDATION FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print("VALIDATION PASSED")
    print(f"Tables: {len(schema.tables)}")
    print(f"Rows: {observed_rows:,}")
    print(f"Formats: {manifest['format_table_counts']}")
    print("Every source table exists exactly once in its assigned native format.")
    print("SQLite integrity: OK; foreign-key violations: 0")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the manifest, schema, physical files, and SQLite integrity.")
    parser.add_argument("--landing", type=Path, default=ROOT / "data" / "landing")
    parser.add_argument("--schema", type=Path, default=ROOT / "schema.md")
    args = parser.parse_args()
    return validate_landing(args.landing, args.schema)


if __name__ == "__main__":
    raise SystemExit(main())
