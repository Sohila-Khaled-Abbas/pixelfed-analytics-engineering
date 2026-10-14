# PixelFed Schema-Exact Synthetic Lakehouse

A schema-driven data engineering project that generates synthetic datasets for **all 54 tables** documented in `schema.md`. The Markdown schema is the contract for table names, column names and order, the MySQL type labels present in the file, nullability markers, primary keys, declared uniqueness/indexes, and documented relationships.

> **All records are synthetic.** This generator is for analytics development, Power BI modeling, and portfolio demonstrations. Values resembling credentials, tokens, private keys, IPs, user agents, or contact details are mock values and must not be used to authenticate to any service.

## Exact default landing path

The generator defaults to the requested Windows directory:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
```

No output directory argument is required to use that location. You can override it with `--output-dir` when testing.

## Install

Run in PowerShell from this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Recommended first run

A smaller run is best for verifying Power BI ingestion:

```powershell
python .\pixelfed_schema_lakehouse_generator.py `
    --scale 0.01 `
    --seed 42 `
    --as-of 2026-10-14T12:00:00Z `
    --output-dir "D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing_test"
```

## Full default run

This writes the full dataset to the exact landing path above:

```powershell
python .\pixelfed_schema_lakehouse_generator.py `
    --seed 42 `
    --as-of 2026-10-14T12:00:00Z
```

The default export list is `csv,csv_gz,parquet,jsonl,feather,sqlite`. `parquet` and `feather` require the packages in `requirements.txt`. If you need a SQLite/CSV-only run, you can omit Arrow-based formats:

```powershell
python .\pixelfed_schema_lakehouse_generator.py `
    --seed 42 `
    --as-of 2026-10-14T12:00:00Z `
    --formats csv,csv_gz,jsonl,sqlite
```

Available formats: `csv`, `csv_gz`, `parquet`, `jsonl`, `feather`, and `sqlite`.

## Output layout

```text
landing/
├── csv/                         # 54 uncompressed CSVs; easiest starting point for Power BI
├── csv_gz/                      # 54 compressed CSV copies
├── parquet/                     # 54 typed analytical files (full export)
├── jsonl/                       # Event-oriented tables as JSON Lines
├── feather/                     # Direct messages as Feather IPC
├── sqlite/
│   └── pixelfed_schema_replica.sqlite  # All 54 tables in one relational file
└── metadata/
    ├── schema.md
    ├── schema_contract.json
    ├── manifest.json
    ├── row_counts.csv
    └── data_quality_report.json
```

## Schema fidelity

- Every generated table uses exactly the column names and order in `schema.md`.
- The parser requires exactly 54 documented table definitions and fails rather than silently generating a partial schema.
- Data-quality validation checks output column order, NOT NULL fields, primary-key uniqueness, documented unique indexes, and relationship values.
- SQLite contains all 54 tables, with constraints/indexes derived from schema metadata and relationships.
- The supplied Markdown does not specify MySQL column lengths (for example, `varchar(255)`) or the allowed members of `enum`; those missing details cannot be reconstructed faithfully. Values for enum-like columns are synthetic and representative, not a claim about the complete application enum.
- The Markdown relationship list has a few semantically unusual links. Those links are honored as documented for schema-based validation rather than silently rewriting the source diagram.

## Power BI import

1. Open Power BI Desktop and create a text parameter named `pLakehousePath` with this value:

   ```text
   D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
   ```

2. For each `.pq` file in `powerbi_m_sources`, create a **Blank Query**, open **Advanced Editor**, paste the file content, and name the query as its filename (for example, `stg_users`). These source queries read the uncompressed files in `csv/` and apply the column types declared in the Markdown schema.
3. Disable load for the staging queries after checking data quality.
4. Create curated queries for the Power BI semantic model. Exclude security/credential-style columns such as `password`, `remember_token`, OAuth secrets/tokens, `private_key`, `public_key`, `2fa_secret`, backup codes, session payloads, and raw IP/user-agent fields unless explicitly required for a documented security-analysis use case.
5. Build separate fact tables for events (likes, comments, follows, notifications) and dimensions for users/profiles, statuses, hashtags, dates, and related entities. Do not flatten multiple one-to-many facts together or you may multiply event counts.
6. Use `metadata/data_quality_report.json` and `metadata/row_counts.csv` to document row counts and quality checks.

## Repeatability

Use the same Python version/dependency set, `--seed`, and `--as-of` timestamp for stable synthetic values. Do not commit the generated landing-zone data or database to Git unless the repository specifically needs a small synthetic sample.
