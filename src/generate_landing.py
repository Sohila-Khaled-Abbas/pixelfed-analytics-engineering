#!/usr/bin/env python3
"""Generate schema-faithful synthetic PixelFed data in a mixed-format landing zone.

Every schema table is written to exactly one native format. No input file is converted
from one format into another: each output is serialized directly from the generated rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from schema_generator_core import SchemaDrivenGenerator, _quote, parse_as_of, parse_schema  # noqa: E402

LOG = logging.getLogger("pixelfed_lakehouse")
DEFAULT_OUTPUT = ROOT / "data" / "landing"

# Learning-focused table-to-format allocation. These are *not* conversion rules:
# rows are generated once in memory and written directly to the assigned format.
FORMAT_GROUPS: dict[str, tuple[str, ...]] = {
    "csv_gz": (
        "statuses",
        "likes",
        "comments",
        "media",
        "followers",
        "status_hashtags",
        "mentions",
        "story_views",
        "hashtag_follows",
        "reports",
        "report_comments",
    ),
    "csv": (
        "users",
        "profiles",
        "hashtags",
        "bookmarks",
        "collections",
        "collection_items",
        "circles",
        "circle_profiles",
        "avatars",
        "stories",
    ),
    "jsonl": (
        "account_logs",
        "activities",
        "failed_jobs",
        "jobs",
        "mod_logs",
        "notifications",
        "report_logs",
        "websockets_statistics_entries",
    ),
    "json": (
        "direct_messages",
        "discover_category_hashtags",
        "import_datas",
        "import_jobs",
        "profile_sponsors",
    ),
    "xlsx": (
        "discover_categories",
        "instances",
        "migrations",
        "places",
        "oauth_personal_access_clients",
        "user_devices",
        "user_settings",
    ),
    # The final thirteen operational/auth-adjacent tables live in a single SQLite database.
    "sqlite": (
        "contacts",
        "email_verifications",
        "follow_requests",
        "newsroom",
        "oauth_access_tokens",
        "oauth_auth_codes",
        "oauth_clients",
        "oauth_refresh_tokens",
        "pages",
        "password_resets",
        "sessions",
        "user_filters",
        "user_invites",
    ),
}


def build_table_format_map(schema: Any) -> dict[str, str]:
    assignment: dict[str, str] = {}
    for fmt, names in FORMAT_GROUPS.items():
        for name in names:
            if name in assignment:
                raise ValueError(f"Table {name!r} is assigned to multiple formats")
            assignment[name] = fmt
    missing = set(schema.tables) - set(assignment)
    unknown = set(assignment) - set(schema.tables)
    if missing or unknown:
        raise ValueError(f"Format assignment mismatch. Missing={sorted(missing)}, unknown={sorted(unknown)}")
    return assignment


def jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value


def native_row(row: dict[str, Any], table_name: str, schema: Any, parse_json_columns: bool = True) -> dict[str, Any]:
    """Convert datetime values to ISO strings and JSON-typed string values to native JSON."""
    out: dict[str, Any] = {}
    for col in schema.tables[table_name].columns:
        value = row.get(col.name)
        if parse_json_columns and col.mysql_type.lower() == "json" and isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        out[col.name] = jsonable(value)
    return out


def write_csv_gz(generator: SchemaDrivenGenerator, table_name: str) -> Path:
    return generator._write_csv(table_name, compressed=True)


def write_csv(generator: SchemaDrivenGenerator, table_name: str) -> Path:
    return generator._write_csv(table_name, compressed=False)


def write_jsonl(generator: SchemaDrivenGenerator, table_name: str) -> Path:
    out_dir = generator.output_dir / "jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{table_name}.jsonl"
    tmp = path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as stream:
        for row in generator.datasets[table_name]:
            stream.write(
                json.dumps(native_row(row, table_name, generator.schema), ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
    tmp.replace(path)
    return path


def write_json(generator: SchemaDrivenGenerator, table_name: str) -> Path:
    out_dir = generator.output_dir / "json"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{table_name}.json"
    tmp = path.with_suffix(".json.tmp")
    rows = [native_row(row, table_name, generator.schema) for row in generator.datasets[table_name]]
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def write_xlsx(generator: SchemaDrivenGenerator, table_name: str) -> Path:
    out_dir = generator.output_dir / "xlsx"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{table_name}.xlsx"
    tmp = out_dir / f"{table_name}.tmp.xlsx"
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(title=table_name[:31])
    columns = generator.schema.tables[table_name].column_names
    sheet.append(columns)
    for row in generator.datasets[table_name]:
        sheet.append(
            [
                jsonable(row.get(col))
                if not isinstance(row.get(col), (dict, list))
                else json.dumps(row.get(col), ensure_ascii=False)
                for col in columns
            ]
        )
    workbook.save(tmp)
    tmp.replace(path)
    return path


def write_sqlite_subset(generator: SchemaDrivenGenerator, table_names: tuple[str, ...]) -> Path:
    out_dir = generator.output_dir / "sqlite"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "pixelfed_operational_tables.sqlite"
    tmp = out_dir / "pixelfed_operational_tables.tmp.sqlite"
    if tmp.exists():
        tmp.unlink()
    selected = set(table_names)
    conn = sqlite3.connect(tmp)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        # Create only the tables allocated to SQLite. Keep relationships enforceable when
        # both the parent and child tables are in this same physical SQLite source.
        for table_name in table_names:
            table = generator.schema.tables[table_name]
            col_defs: list[str] = []
            for col in table.columns:
                definition = f"{_quote(col.name)} {col.mysql_type.upper()}"
                if not col.nullable or col.primary_key:
                    definition += " NOT NULL"
                if col.primary_key:
                    definition += " PRIMARY KEY"
                if col.unique and not col.primary_key:
                    definition += " UNIQUE"
                col_defs.append(definition)
            fk_defs: list[str] = []
            for (child_table, child_col), (parent_table, parent_col) in generator.references.items():
                if child_table == table_name and parent_table in selected:
                    fk_defs.append(
                        f"FOREIGN KEY ({_quote(child_col)}) REFERENCES {_quote(parent_table)}({_quote(parent_col)}) DEFERRABLE INITIALLY DEFERRED"
                    )
            conn.execute(f"CREATE TABLE {_quote(table_name)} ({', '.join(col_defs + fk_defs)})")

        for table_name in table_names:
            table = generator.schema.tables[table_name]
            for col in table.columns:
                if col.indexed and not col.primary_key:
                    conn.execute(
                        f"CREATE INDEX IF NOT EXISTS {_quote(f'idx_{table_name}_{col.name}')} ON {_quote(table_name)} ({_quote(col.name)})"
                    )
        for table_name, cols, is_unique, index_name in generator.schema.indexes:
            if table_name not in selected:
                continue
            unique_sql = "UNIQUE " if is_unique else ""
            conn.execute(
                f"CREATE {unique_sql}INDEX IF NOT EXISTS {_quote(index_name)} ON {_quote(table_name)} ({', '.join(_quote(c) for c in cols)})"
            )

        conn.execute("BEGIN")
        conn.execute("PRAGMA defer_foreign_keys = ON")
        for table_name in table_names:
            columns = generator.schema.tables[table_name].column_names
            placeholders = ",".join("?" for _ in columns)
            statement = (
                f"INSERT INTO {_quote(table_name)} ({', '.join(_quote(c) for c in columns)}) VALUES ({placeholders})"
            )
            rows = [
                tuple(generator._format_row_value(row.get(c)) for c in columns)
                for row in generator.datasets[table_name]
            ]
            conn.executemany(statement, rows)
        conn.commit()
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"SQLite FK violations: {violations[:10]}")
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise ValueError(f"SQLite integrity_check returned {result}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    tmp.replace(path)
    return path


def write_manifest(
    generator: SchemaDrivenGenerator, report: dict[str, Any], assignment: dict[str, str], paths: list[str]
) -> None:
    metadata = generator.output_dir / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    # Extend the core report with the one-table/one-format contract.
    report["table_storage"] = {
        table: {
            "format": fmt,
            "file": (
                f"{fmt}/{table}.{ {'csv': 'csv', 'csv_gz': 'csv.gz', 'jsonl': 'jsonl', 'json': 'json', 'xlsx': 'xlsx'}.get(fmt, '') }"
                if fmt != "sqlite"
                else "sqlite/pixelfed_operational_tables.sqlite"
            ),
        }
        for table, fmt in assignment.items()
    }
    report["format_table_counts"] = dict(Counter(assignment.values()))
    report["output_files"] = paths
    report["unique_physical_representation_per_table"] = True
    (metadata / "data_quality_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    contract = {
        "database": "mysql",
        "table_count": len(generator.schema.tables),
        "tables": {
            name: {
                "storage_format": assignment[name],
                "columns": [
                    {
                        "name": c.name,
                        "mysql_type": c.mysql_type,
                        "nullable": c.nullable,
                        "primary_key": c.primary_key,
                        "unique": c.unique,
                        "indexed": c.indexed,
                        "foreign_key_marker": c.foreign_key_marker,
                    }
                    for c in table.columns
                ],
            }
            for name, table in generator.schema.tables.items()
        },
        "relationships": [
            {"child_table": child, "child_column": ccol, "parent_table": parent, "parent_column": pcol}
            for (child, ccol), (parent, pcol) in generator.references.items()
        ],
    }
    (metadata / "schema_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")

    manifest = {
        "project": "PixelFed Analytics Engineering",
        "output_directory": str(generator.output_dir),
        "schema_table_count": len(generator.schema.tables),
        "total_rows": sum(len(rows) for rows in generator.datasets.values()),
        "seed": generator.seed,
        "scale": generator.scale,
        "as_of_utc": generator.run_at.isoformat() + "Z",
        "formats": sorted(set(assignment.values())),
        "format_table_counts": dict(Counter(assignment.values())),
        "table_storage": report["table_storage"],
        "files": paths,
        "unique_physical_representation_per_table": True,
        "note": "Synthetic records; each schema table is written directly to exactly one assigned format. No format-to-format conversion is performed.",
    }
    (metadata / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    with (metadata / "row_counts.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["table_name", "row_count", "column_count", "storage_format", "source_path"])
        for name, table in generator.schema.tables.items():
            item = report["table_storage"][name]
            writer.writerow([name, len(generator.datasets[name]), len(table.columns), assignment[name], item["file"]])


def clean_previous_generated_files(output: Path, schema: Any) -> None:
    """Remove stale generator-owned table outputs to prevent cross-format duplicates.

    Only known table filenames in managed format folders and known metadata files are
    touched. Unrelated user files are left intact.
    """
    suffixes = {"csv": ".csv", "csv_gz": ".csv.gz", "jsonl": ".jsonl", "json": ".json", "xlsx": ".xlsx"}
    for folder, suffix in suffixes.items():
        target_dir = output / folder
        if not target_dir.exists():
            continue
        for table_name in schema.tables:
            candidate = target_dir / f"{table_name}{suffix}"
            if candidate.is_file():
                candidate.unlink()
        # Remove only temporary files produced by interrupted runs.
        for candidate in target_dir.glob("*.tmp"):
            if candidate.is_file():
                candidate.unlink()
    sqlite_dir = output / "sqlite"
    for name in ("pixelfed_operational_tables.sqlite", "pixelfed_operational_tables.tmp.sqlite"):
        candidate = sqlite_dir / name
        if candidate.is_file():
            candidate.unlink()
    metadata_dir = output / "metadata"
    for name in ("manifest.json", "row_counts.csv", "schema_contract.json", "data_quality_report.json", "schema.md"):
        candidate = metadata_dir / name
        if candidate.is_file():
            candidate.unlink()


def export_mixed(
    generator: SchemaDrivenGenerator, assignment: dict[str, str], report: dict[str, Any], schema_path: Path
) -> None:
    output = generator.output_dir
    output.mkdir(parents=True, exist_ok=True)
    clean_previous_generated_files(output, generator.schema)
    paths: list[str] = []
    sqlite_tables = tuple(name for name, fmt in assignment.items() if fmt == "sqlite")

    for table_name, fmt in assignment.items():
        if fmt == "csv_gz":
            path = write_csv_gz(generator, table_name)
        elif fmt == "csv":
            path = write_csv(generator, table_name)
        elif fmt == "jsonl":
            path = write_jsonl(generator, table_name)
        elif fmt == "json":
            path = write_json(generator, table_name)
        elif fmt == "xlsx":
            path = write_xlsx(generator, table_name)
        elif fmt == "sqlite":
            continue  # written once below as one relational source with multiple tables
        else:
            raise ValueError(f"Unsupported format {fmt} for {table_name}")
        paths.append(str(path.relative_to(output)))

    if sqlite_tables:
        path = write_sqlite_subset(generator, sqlite_tables)
        paths.append(str(path.relative_to(output)))

    # Keep schema contract in the landing zone, so the files remain self-describing.
    (output / "metadata").mkdir(parents=True, exist_ok=True)
    shutil.copy2(schema_path, output / "metadata" / "schema.md")
    write_manifest(generator, report, assignment, paths)

    # SQLite tables need a per-table row count in manifest even though they share one DB file.
    manifest_path = output / "metadata" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for table_name, fmt in assignment.items():
        if fmt == "sqlite":
            manifest["table_storage"][table_name]["file"] = "sqlite/pixelfed_operational_tables.sqlite"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate schema-exact PixelFed datasets in mixed native formats.")
    parser.add_argument("--schema", type=Path, default=ROOT / "schema.md")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--scale", type=float, default=1.0, help="Use 0.01 for a small smoke test")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--as-of", type=str, default="2026-10-14T12:00:00Z")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s | %(levelname)s | %(message)s")

    schema_path = args.schema.resolve()
    schema = parse_schema(schema_path)
    assignment = build_table_format_map(schema)
    generator = SchemaDrivenGenerator(
        schema=schema,
        output_dir=args.output_dir,
        seed=args.seed,
        scale=args.scale,
        as_of=parse_as_of(args.as_of),
        formats=set(),  # export uses the fixed one-table/one-format map above
    )
    generator.generate()
    report = generator._validate_datasets()
    export_mixed(generator, assignment, report, schema_path)

    # Validate one physical representation per table and metadata consistency.
    manifest = json.loads((args.output_dir / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_table_count"] == 54
    assert set(manifest["table_storage"]) == set(schema.tables)
    assert manifest["unique_physical_representation_per_table"] is True
    assert sum(manifest["format_table_counts"].values()) == 54
    LOG.info(
        f"SUCCESS: {len(schema.tables)} tables, {manifest['total_rows']:,} rows, formats={manifest['format_table_counts']}"
    )
    LOG.info("Output directory: %s", args.output_dir)
    LOG.info("Manifest: %s", args.output_dir / "metadata" / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
