# Power BI Import Guide — Mixed Native Formats

The goal is to practice importing different *source* formats. Do not convert all files into a single format. Each table exists in one assigned format, and each prepared M query under `powerbi/m_queries/` points to that original source.

## 1. Generate the landing zone

Create and activate a virtual environment, install `requirements.txt`, then run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\src\generate_landing.py --scale 0.01 --output-dir "D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing_test"
```

After the smoke test succeeds, generate the full data by omitting `--scale` and `--output-dir` to use:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
```

## 2. Configure Power BI

In Power BI Desktop, use **Transform data → Manage Parameters → New Parameter**.

- Name: `pLakehousePath`
- Type: Text
- Value: `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`

For SQLite access, install a compatible **64-bit SQLite ODBC driver** and create a User DSN called `PixelFedSQLite` pointing to `sqlite\pixelfed_operational_tables.sqlite`. Power BI Desktop bitness and ODBC driver bitness must match.

## 3. Import the mixed-format sources

The directory and file extension show how each table is stored. All formats are read directly; no file-to-file conversion is performed.

| Format | Tables | Power Query method | Skills exercised |
|---|---:|---|---|
| CSV.GZ | 11 | `Binary.Decompress(..., Compression.GZip)` → `Csv.Document` | compressed batch ingestion |
| CSV | 10 | `Csv.Document` → `Table.PromoteHeaders` | delimited files and explicit types |
| JSONL | 8 | `Lines.FromBinary` → `Json.Document` per line → `Table.FromRecords` | line-delimited event data |
| JSON array | 5 | `Json.Document` → `Table.FromRecords` | nested and semi-structured fields |
| XLSX | 7 | `Excel.Workbook` → select sheet → promote headers | spreadsheet source ingestion |
| SQLite | 13 | `Odbc.Query` against `PixelFedSQLite` | relational queries and ODBC setup |
| **Total** | **54** | | every source table represented once |

## 4. Add the prepared staging queries

1. Open `powerbi/m_queries/`.
2. In Power BI, choose **Transform data → New Source → Blank Query → Advanced Editor**.
3. Paste a `.pq` file's contents and name the query `stg_<table>` as given in its filename.
4. Ensure `pLakehousePath` exists and the `PixelFedSQLite` DSN is configured before refreshing SQLite queries.
5. Start with the core tables `stg_profiles`, `stg_statuses`, `stg_likes`, `stg_comments`, `stg_media`, `stg_followers`, and `stg_status_hashtags`; then add remaining tables.

## 5. Validate the ingestion

Compare results against `data/landing/metadata/row_counts.csv` and `manifest.json`. Check these before building visuals:

- one staging query for every schema table;
- output row count equals the manifest's table row count;
- column names and order match `schema.md`;
- IDs have integer types, timestamps have Date/Time types, numeric values are numeric, flags remain 0/1 values, and JSON payloads are text or explicitly expanded structures;
- primary and unique keys remain unique and non-null;
- cross-format foreign keys reconcile across staging queries.

Turn off **Enable load** for staging queries after your curated dimensions and facts are built. Use separate fact tables at their declared grain to avoid multiplying counts.

## 6. Security and governance

The data is synthetic, but use the project to practice column minimization: do not expose `password`, `secret`, token, private-key, session-payload, IP address, user-agent, or unnecessary email columns in report-facing models. Keep the complete schema only in staging where needed for source-contract validation.

## Troubleshooting

- **Path not found:** verify `pLakehousePath`; avoid manually adding a second `landing` segment.
- **CSV.GZ error:** use the supplied query's `Binary.Decompress` step; do not open compressed content as ordinary CSV text.
- **JSONL parse error:** parse each non-empty line separately rather than treating the whole file as one JSON array.
- **Excel sheet not found:** use the exact table name as the worksheet name.
- **ODBC source error:** check the 64-bit SQLite driver, the DSN name, and the SQLite path.
- **Date parsing error:** inspect the source string and explicit culture; the generator writes timestamps in an ISO-like format.
