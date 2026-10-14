# PixelFed Synthetic Data Lakehouse Generator

A reproducible, configurable Python generator for synthetic PixelFed-style datasets. It creates relational dimensions, engagement facts, graph relationships, and semi-structured activity streams, validates the generated data, and writes a manifest plus data-quality report.

> All generated records are synthetic. They are intended for learning, demos, pipeline development, and testing—not as real user data or a production PixelFed export.

## Requirements

- Python 3.10+
- pandas
- NumPy
- Faker
- PyArrow (Parquet and Feather export)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

Generate the default dataset:

```bash
python pixelfed_lakehouse_generator.py
```

Generate a smaller smoke-test dataset:

```bash
python pixelfed_lakehouse_generator.py --scale 0.01 --output-dir ./pixelfed_test
```

Repeat the same generated records by pinning both the random seed and the UTC `--as-of` anchor:

```bash
python pixelfed_lakehouse_generator.py --seed 42 --as-of 2026-10-14T12:00:00Z --output-dir ./pixelfed_repeatable
```

Use `python pixelfed_lakehouse_generator.py --help` for supported options.

## Output layout

```text
pixelfed_lakehouse_landing/
├── batch_csv_gz/        # users, profiles, hashtags
├── columnar_parquet/    # statuses, media, likes, comments, followers
├── streaming_jsonl/     # account_logs, activities, notifications
├── binary_feather/      # direct_messages (Apache Feather IPC)
├── relational_sqlite/   # pixelfed_source_snapshot.sqlite (12 tables)
├── manifest.json
└── data_quality_report.json
```

Timestamps in tabular datasets represent UTC but are timezone-naive for compatibility. JSONL timestamps are ISO-formatted. SQLite timestamps are ISO text. Feather files use the `.feather` extension (not `.arrow`) to match the actual file format.

## Data-engineering safeguards

- Seeded NumPy, Python, and Faker random generators; optional fixed `--as-of` timestamp for repeatable values and timestamps.
- Exact configured row counts for generated tables, with unique profile/status like pairs and unique non-self follow pairs.
- Referential-integrity and polymorphic-reference checks, primary-key and uniqueness checks, payload JSON checks, and future-timestamp checks.
- SQLite primary keys, selected foreign keys, business-key indexes, join indexes, `PRAGMA foreign_key_check`, and `PRAGMA integrity_check`.
- Per-file temporary writes followed by atomic rename, plus a run manifest and data-quality report.

## Important note

PyArrow is a required dependency for `.parquet` and `.feather` outputs. If it is missing, the pipeline reports the installation command rather than silently skipping those formats.
