# Import the PixelFed mixed-format landing zone with TMDL

This project includes a **TMDL View script** that defines 54 staging tables in a Power BI semantic model. Each table's Import partition embeds its corresponding Power Query M (`.pq`) logic, so Power BI reads the table from its assigned native format instead of converting it to a common file format.

> Important: TMDL View applies semantic-model metadata. It does **not** load/refresh source data as part of applying the script. After applying the script, configure local sources and run **Refresh**. See Microsoft's [TMDL View documentation](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view).

## Files to use

- `powerbi/tmdl/01_Create_Core_Staging_Tables.tmdl` — a small first-run script for `users`, `profiles`, `statuses`, `likes`, `comments`, `media`, `hashtags`, and `status_hashtags`. Use this for a controlled smoke test.
- `powerbi/tmdl/Create_Staging_Tables.tmdl` — full staging model: 54 tables and 555 columns.
- `src/build_tmdl_script.py` — reproducibly builds the TMDL scripts from `schema.md` and the project's `powerbi/m_queries/stg_*.pq` files.
- `config_table_format_assignment.json` — source-of-truth table-to-format assignment.

## 1. Extract the landing zone

Extract the dataset ZIP into:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\
```

The archive includes a top-level `landing` directory, so the final landing path becomes:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
```

Expected format directories include `csv`, `csv_gz`, `jsonl`, `json`, `xlsx`, `sqlite`, and `metadata`.

## 2. Configure SQLite before the full refresh

Thirteen staging queries read the SQLite file through ODBC.

1. Install a compatible **64-bit SQLite ODBC driver**. Its bitness must match Power BI Desktop.
2. Open **ODBC Data Sources (64-bit)** from the Windows Start menu.
3. Under **User DSN**, choose **Add** and select the installed SQLite driver.
4. Set the Data Source Name to `PixelFedSQLite`.
5. Set the database file to:

   ```text
   D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing\sqlite\pixelfed_operational_tables.sqlite
   ```

6. Save the DSN and use the driver's test button if available.

The TMDL model queries already reference `dsn=PixelFedSQLite`. The DSN needs to exist before you refresh the complete model. If you do not configure it yet, test the core script first; it does not include SQLite tables.

## 3. Start a new Power BI model

1. Open Power BI Desktop and create a new blank report.
2. Save it somewhere inside the project, for example `powerbi/PixelFedAnalytics.pbix`.
3. Open **TMDL view** from the left navigation.
4. Create a new TMDL script tab.
5. Open `powerbi/tmdl/01_Create_Core_Staging_Tables.tmdl` in a text editor and copy its entire contents into the TMDL View editor.
6. Check that `pLakehousePath` at the top is set to your exact `data\landing` path. Change it before applying if your path differs.
7. Click **Preview** first. Review the changes; then click **Apply** if the script is valid.
8. Run **Home → Refresh**. This runs the M partitions and loads the eight core tables from the landing-zone files.

Microsoft notes that TMDL View changes model metadata, and that source changes requiring data refresh must be followed by a manual refresh: [Work with TMDL view](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view).

## 4. Apply the full 54-table script

After the core smoke test succeeds:

1. Return to TMDL view and create another new script tab.
2. Copy all of `powerbi/tmdl/Create_Staging_Tables.tmdl` into it.
3. Preview the script and make sure it defines `pLakehousePath` and tables named `stg_<schema_table>`.
4. Apply the script.
5. Select **Home → Refresh**. The full model includes the 13 SQLite tables, so ensure the ODBC DSN from Step 2 exists first.
6. If prompted about local file or ODBC credentials/privacy levels, select the appropriate local-source settings and keep the sources consistently classified. The data is synthetic; avoid using real credentials in the mock files.

`createOrReplace` replaces the listed objects and descendants. Use this in a new/empty model for the first load. If you are applying it to an existing model with tables named `stg_<table>`, back up the model first.

## 5. Validate the loaded data

Compare loaded row counts against:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing\metadata\row_counts.csv
```

Check all of the following:

- There are 54 staging tables named `stg_<schema_table>` after the full refresh.
- Each table's columns match `schema.md` in name and source order.
- Row counts match the generated `metadata/row_counts.csv` file.
- Primary keys have unique, non-null values.
- Cross-table keys reconcile where the schema declares relationships.
- JSON/JSONL columns are kept as text in staging unless you explicitly expand their structures.

The TMDL script declares primary-key columns as `isKey`, but deliberately does not create relationships. Build and validate relationships in a separate curated model step rather than blindly linking every source FK into a report model.

## 6. Build the analytics-engineering layer

Keep these 54 `stg_` tables as source/staging tables. Once validated:

1. Disable **Enable load** for staging tables if you create separate curated queries.
2. Reference staging queries to build `DimProfile`, `DimStatus`, `DimHashtag`, `DimDate`, `FactPostMetrics`, `FactLikes`, `FactComments`, `FactMedia`, `FactFollows`, and `BridgeStatusHashtag`.
3. Keep facts at their own grain; do not flatten likes, comments, and media into one table.
4. Exclude sensitive-looking columns (passwords, tokens, secrets, private keys, session payloads, IP addresses, user agents, and unnecessary email fields) from report-facing tables, even though the data is synthetic.
5. Add DAX measures only after key uniqueness, relationship cardinality, and row counts pass validation.

## 7. Rebuild the TMDL script after source changes

If `schema.md` or the `.pq` source queries change, rebuild the script from the project root:

```powershell
python .\src\build_tmdl_script.py
```

To rebuild the smaller core script:

```powershell
python .\src\build_tmdl_script.py `
  --tables users,profiles,statuses,likes,comments,media,hashtags,status_hashtags `
  --output .\powerbi\tmdl\01_Create_Core_Staging_Tables.tmdl
```

## Troubleshooting

- **`TMDL Format Error: InvalidLineType — Unexpected line type: Other` on a `//` line:** TMDL View script files do not accept C-style `//` comment lines. The corrected scripts remove those lines, use `///` only as TMDL documentation directly above table definitions, and indent objects beneath `createOrReplace` according to TMDL script syntax. Re-copy the corrected file from `powerbi/tmdl/` rather than reusing an older copy.
- **File not found:** confirm the exact parameter path and ensure there is not a duplicated `landing\landing` segment.
- **`Expression.Error` for `pLakehousePath`:** make sure the shared M expression is in the script and was applied.
- **ODBC IM002 / data source not found:** create a 64-bit User DSN named exactly `PixelFedSQLite`.
- **The tables appear but contain no data:** applying TMDL changes metadata only; run **Refresh**.
- **Apply fails:** inspect the TMDL View Problems/Output panes. Use the core script first, apply it, refresh, and then apply the full script.
- **Dataset row-count mismatch:** compare `row_counts.csv` and the `metadata/data_quality_report.json` before building visuals.

## Official references

- [TMDL View in Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view)
- [TMDL language and partition M expressions](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=asallproducts-allversions)
- [Power BI Project overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
