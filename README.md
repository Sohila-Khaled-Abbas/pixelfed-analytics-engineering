# PixelFed Analytics Engineering

**Suggested GitHub repository:** `pixelfed-analytics-engineering`  
**Project type:** schema-driven synthetic lakehouse + Power BI semantic model  
**Data source contract:** the supplied 54-table PixelFed MySQL schema in [`schema.md`](schema.md)

## Overview

This portfolio project simulates an Analytics Engineering workflow from a relational source schema to a mixed-format landing zone and a Power BI semantic model. It generates deterministic synthetic records, preserves the documented table/column order, validates keys and relationships, and demonstrates loading different physical formats without converting every source into one file type.

![Project architecture](assets/Architecture.svg)

> **Important format rule:** every schema table has exactly one assigned physical format. The generator creates each output directly from the in-memory synthetic rows. It does **not** read a `.csv.gz` file and convert it to Parquet, and it does not emit duplicate copies of a table in other formats.

## Learning objectives

- Translate an operational MySQL schema into a source contract and data dictionary.
- Generate repeatable synthetic data with explicit seed and reference timestamp.
- Practice ingestion of CSV, compressed CSV (`.csv.gz`), JSON arrays, JSON Lines, Excel workbooks and SQLite.
- Build reusable Power Query M staging queries and parameterized source paths.
- Validate schema fidelity, row counts, primary/unique keys and referential integrity.
- Design a curated Power BI model with grain-aware facts and conformed dimensions.
- Keep sensitive-looking synthetic fields out of report-facing semantic models.

## Mixed-format allocation

| Format | Tables | Learning focus |
| --- | ---: | --- |
| `.csv.gz` | 11 | Large batch tables, decompression in Power Query |
| `.csv` | 10 | Tabular imports and data types |
| `.jsonl` | 8 | Event/log records, one JSON object per line |
| `.json` | 5 | JSON document arrays and nested JSON values |
| `.xlsx` | 7 | Business extracts and small reference/configuration tables |
| `.sqlite` | 13 | Relational ingestion through an ODBC source |
| **Total** | **54** | Every table is assigned once; no duplicate table exports |

The table-level mapping is documented in [`config_table_format_assignment.json`](config_table_format_assignment.json), [`docs/FORMAT_CATALOG.md`](docs/FORMAT_CATALOG.md), and generated `data/landing/metadata/manifest.json`.

## Repository layout

```text
pixelfed-analytics-engineering/
├── assets/                 # Architecture SVG and project visuals
├── data/                   # Generated landing data is local and Git-ignored
├── database/               # SQLite notes and SQL examples
├── docs/                   # Architecture, data dictionary, quality and import guides
├── powerbi/                # 54 Power Query M staging queries and model notes
├── src/                    # Reproducible schema-driven generator
├── tests/                  # Assignment and output-contract tests
├── schema.md               # Canonical 54-table schema contract
├── config_table_format_assignment.json
├── requirements.txt
├── .gitignore
└── README.md
```

Local `.git` metadata is created by Git and is not part of a downloadable repository archive. `.venv` is a local Python environment and is excluded by `.gitignore`.

## Quick start (Windows / PowerShell)

1. Clone the repository and open its root folder.
2. Create the Python environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

1. Test the full schema contract at a small scale first:

```powershell
python .\src\generate_landing.py `
  --schema .\schema.md `
  --scale 0.01 `
  --seed 42 `
  --as-of 2026-10-14T12:00:00Z `
  --output-dir "D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing_test"
```

1. Generate the full dataset at the exact requested output path:

```powershell
python .\src\generate_landing.py `
  --schema .\schema.md `
  --seed 42 `
  --as-of 2026-10-14T12:00:00Z
```

Default landing directory:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
```

1. Follow [`docs/POWER_BI_IMPORT_GUIDE.md`](docs/POWER_BI_IMPORT_GUIDE.md) to import the different formats and use the prepared staging queries in `powerbi/m_queries/`.

## Data quality and reproducibility

Each run writes `manifest.json`, `row_counts.csv`, `schema_contract.json`, and `data_quality_report.json`. Reuse the same `--seed` and `--as-of` to keep generated values and timestamps reproducible in the same dependency environment. The generator fails clearly if it detects schema or key/relationship quality problems.

## Modeling approach

Staging preserves source shape and source keys. Curated dimensions and facts should be separate from staging. Start with `DimDate`, `DimProfile`, and `DimStatus`; then model `FactPostMetrics`, `FactLikes`, `FactComments`, `FactMedia`, and `FactFollows` at their natural grain. Do not flatten one-to-many facts into a single table, since joining likes, comments, and media can inflate counts.

See [`docs/POWER_BI_MODEL_GUIDE.md`](docs/POWER_BI_MODEL_GUIDE.md) and [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## Data governance

All values are synthetic and intended only for learning. Credential-like values, tokens, IP addresses, user-agent strings and private-key-like fields are nonfunctional mock data. Do not commit full generated landing files, the SQLite database, `.venv`, or local Power BI cache files. Keep credential-style fields and unnecessary PII out of report-facing models.

## License and source note

This repository is a synthetic engineering exercise based on the supplied schema documentation. It does not bundle PixelFed application source code or real user data. Add a repository license only after confirming the license you want to use for your own project artifacts.
