#!/usr/bin/env python3
"""Validate the mixed-format landing zone against its manifest and schema contract."""
from __future__ import annotations
import argparse, csv, gzip, json, sqlite3, sys
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from schema_generator_core import parse_schema
from generate_landing import build_table_format_map

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--landing',type=Path,default=ROOT/'data'/'landing')
    parser.add_argument('--schema',type=Path,default=ROOT/'schema.md')
    args=parser.parse_args()
    landing=args.landing
    schema=parse_schema(args.schema)
    expected=build_table_format_map(schema)
    manifest=json.loads((landing/'metadata'/'manifest.json').read_text(encoding='utf-8'))
    if set(manifest['table_storage']) != set(schema.tables): raise SystemExit('FAIL: manifest table set does not match schema')
    if {k:v['format'] for k,v in manifest['table_storage'].items()} != expected: raise SystemExit('FAIL: table-format assignment mismatch')
    observed_rows=0
    errors=[]
    with (landing/'metadata'/'row_counts.csv').open(encoding='utf-8', newline='') as count_stream:
        row_counts={r['table_name']:int(r['row_count']) for r in csv.DictReader(count_stream)}
    sqlite_tables={}
    db_path=landing/'sqlite'/'pixelfed_operational_tables.sqlite'
    if not db_path.exists(): errors.append(f'Missing SQLite database: {db_path}')
    else:
        with sqlite3.connect(db_path) as con:
            names={row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            sqlite_tables=names
            if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok': errors.append('SQLite integrity_check failed')
            fks=con.execute('PRAGMA foreign_key_check').fetchall()
            if fks: errors.append(f'SQLite foreign-key violations: {len(fks)}')
    for table,fmt in expected.items():
        spec=schema.tables[table]
        info=manifest['table_storage'][table]
        physical=info['file']
        row_count=0
        try:
            if fmt in {'csv','csv_gz'}:
                path=landing/physical
                if fmt=='csv_gz':
                    with gzip.open(path,'rt',encoding='utf-8',newline='') as f:
                        reader=csv.reader(f); header=next(reader); row_count=sum(1 for _ in reader)
                else:
                    with path.open('r',encoding='utf-8',newline='') as f:
                        reader=csv.reader(f); header=next(reader); row_count=sum(1 for _ in reader)
                if header != spec.column_names: errors.append(f'{table}: CSV header/column order differs from schema')
            elif fmt in {'json','jsonl'}:
                path=landing/physical
                if fmt=='json':
                    records=json.loads(path.read_text(encoding='utf-8'))
                    row_count=len(records)
                    if records and list(records[0].keys()) != spec.column_names: errors.append(f'{table}: JSON column order/name mismatch')
                else:
                    with path.open(encoding='utf-8') as f:
                        records=[json.loads(line) for line in f if line.strip()]
                    row_count=len(records)
                    if records and list(records[0].keys()) != spec.column_names: errors.append(f'{table}: JSONL column order/name mismatch')
            elif fmt=='xlsx':
                path=landing/physical
                workbook=load_workbook(path,read_only=True,data_only=True)
                ws=workbook[table[:31]]
                values=ws.iter_rows(values_only=True)
                header=list(next(values))
                if header != spec.column_names: errors.append(f'{table}: XLSX column order/name mismatch')
                row_count=sum(1 for _ in values)
                workbook.close()
            elif fmt=='sqlite':
                if table not in sqlite_tables: errors.append(f'{table}: missing from SQLite database')
                with sqlite3.connect(db_path) as con:
                    columns=[r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
                    row_count=con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                if columns != spec.column_names: errors.append(f'{table}: SQLite column order/name mismatch')
            expected_rows=manifest['total_rows'] # table count itself is reported per-table in row_counts.csv
            if row_count != row_counts[table]: errors.append(f'{table}: row count {row_count} != expected {row_counts[table]}')
            observed_rows += row_count
        except Exception as exc:
            errors.append(f'{table}: read/validation error: {exc}')
    # Ensure there are no stale physical copies of a table in a different format folder.
    allowed_extensions = {"csv": ".csv", "csv_gz": ".csv.gz", "json": ".json", "jsonl": ".jsonl", "xlsx": ".xlsx"}
    seen_physical = {}
    for fmt, ext in allowed_extensions.items():
        folder = landing / fmt
        if not folder.exists():
            continue
        for file_path in folder.glob(f"*{ext}"):
            table_name = file_path.name[:-len(ext)]
            if table_name in seen_physical:
                errors.append(f"Duplicate table file {table_name}: {seen_physical[table_name]} and {fmt}/{file_path.name}")
            seen_physical[table_name] = f"{fmt}/{file_path.name}"
    if set(seen_physical) != {t for t, f in expected.items() if f != 'sqlite'}:
        errors.append("Physical file set does not match the table assignment for non-SQLite tables")

    if observed_rows != manifest['total_rows']:
        errors.append(f'Total row mismatch: {observed_rows} != {manifest["total_rows"]}')
    if errors:
        print('VALIDATION FAILED')
        print('\n'.join(f'- {e}' for e in errors))
        return 1
    print('VALIDATION PASSED')
    print(f'Tables: {len(schema.tables)}')
    print(f'Rows: {observed_rows:,}')
    print(f'Formats: {manifest["format_table_counts"]}')
    print('Every source table exists exactly once in its assigned native format.')
    print('SQLite integrity: OK; foreign-key violations: 0')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
