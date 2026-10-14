# Power BI import guide — PixelFed mixed-format lakehouse

This guide imports the datasets generated from the supplied `schema.md` without creating duplicate representations of the same source table.

## 0. Extract the files

Extract the dataset archive's top-level `landing` directory to:

```text
D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
```

The landing directory contains:

- `csv\` — 25 individual CSV tables.
- `jsonl\` — 8 individual event/log tables stored as JSON Lines.
- `sqlite\pixelfed_operational_tables.sqlite` — 21 tables only; no CSV/JSONL table is duplicated inside it.
- `metadata\` — schema contract, manifest, row counts and quality report.

Keep this as your source/landing layer. Do not edit the landing files by hand; change the generator or transform them in Power Query instead.

## 1. Create the Power BI project

1. Open Power BI Desktop and choose **Blank report**.
2. Save it in the repository under `powerbi\`.
3. Select **Transform data** to open Power Query Editor.
4. In Power Query, open **Manage Parameters → New Parameter**.
5. Create a Text parameter named `pLakehousePath`. Set Current Value to:

   ```text
   D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing
   ```

   Do not include a trailing backslash. This parameter is used by all CSV and JSONL source queries.

## 2. Configure SQLite connectivity (once)

The SQLite subset is consumed through Power Query's ODBC connector. Microsoft documents the ODBC connection and `Odbc.Query` pattern here: https://learn.microsoft.com/en-us/power-query/connectors/odbc and https://learn.microsoft.com/en-us/powerquery-m/odbc-query.

1. Install a **64-bit SQLite ODBC driver** that is compatible with your installed Power BI Desktop architecture.
2. Open **ODBC Data Sources (64-bit)** in Windows.
3. Under **User DSN**, select **Add** and choose the installed SQLite driver.
4. Set the DSN name to exactly `PixelFedSQLite`.
5. Point its database/file setting to:

   ```text
   D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing\sqlite\pixelfed_operational_tables.sqlite
   ```
6. Save the DSN and test that the driver opens the file.

If you move the landing folder later, update the DSN to the new SQLite path. The `pLakehousePath` parameter does not configure an ODBC DSN automatically.

## 3. Create the 54 staging queries

The project includes one ready-to-paste Power Query M file per table in `powerbi_m_sources`, all named `stg_<table>.pq`.

For each file you need:

1. In Power Query Editor, select **Home → New Source → Blank Query**.
2. Rename the query to the matching filename without `.pq` (for example, `stg_users`).
3. Open **Home → Advanced Editor**.
4. Replace the editor contents with the contents of that file and select **Done**.
5. Verify the query preview: expected columns, data types and row count.

The M sources use the source type assigned to each schema table:

- **CSV:** `Csv.Document(File.Contents(...))`, header promotion and type conversion.
- **JSONL:** `Lines.FromBinary`, parse each non-empty line with `Json.Document`, create a table, then convert types.
- **SQLite:** `Odbc.Query` using `dsn=PixelFedSQLite` to select the table from the SQLite subset database.

For CSV tables, you can alternatively choose **Get data → Text/CSV**; for JSON Lines use the supplied M pattern because the generic JSON connector can treat a multi-line JSONL file as malformed JSON. Microsoft's JSON connector documentation includes an example of parsing JSON Lines: https://learn.microsoft.com/en-us/power-query/connectors/json. The Text/CSV connector is documented at https://learn.microsoft.com/en-us/power-query/connectors/text-csv.

## 4. Validate staging before modeling

Use `metadata\row_counts.csv` as the expected row-count reference. It lists each table's row count, column count, storage format and location. Use `metadata\data_quality_report.json` for validation results and `metadata\schema_contract.json` to inspect the schema and relationship definitions.

In Power Query, validate:

- Each query has the exact table columns and order expected by `schema.md`.
- Expected row counts match `row_counts.csv`.
- Primary key columns have no blanks or duplicates where the schema says they are keys.
- Foreign-key-like columns match their referenced table after both tables are imported, including relationships that cross from CSV/JSONL into SQLite.
- Date/time columns are typed as Date/Time; do not silently convert IDs to decimal values.
- JSON/text columns remain text unless a separate downstream transformation is deliberately expanding them.

For diagnostics, keep staging queries available in Power Query but use **right-click query → Enable load** to disable model loading for raw staging queries. Create separate referenced queries for curated entities and enable load only on the dimensions/facts needed in the report.

## 5. Keep the semantic model secure and intentional

The source schema includes fields that resemble credentials and private data. Even though this is synthetic, do not bring these into the report model unless there is a specific, documented security-analysis use case. Examples to exclude from curated tables include:

- `users.password`, `users.remember_token`, `users.2fa_secret`, `users.2fa_backup_codes`
- OAuth secrets/tokens, session payloads, password-reset tokens, invite tokens, private/public-key fields
- Raw IP addresses, device fingerprints, full user-agent strings, and unnecessary email/contact fields

Keep a source-faithful staging layer with load disabled; use `Table.SelectColumns` in curated queries to project only approved analytical fields.

## 6. Recommended first curated model

Start with this model rather than loading all 54 raw tables into one flat report:

### Dimensions

- `DimProfile`: one row per `profiles.id`; include selected descriptive attributes only.
- `DimUser`: one row per `users.id`; exclude security/contact fields unless justified.
- `DimStatus`: one row per `statuses.id`; keep author profile, type, visibility, scope, NSFW flag, language, and created/deleted timestamps.
- `DimHashtag`: one row per `hashtags.id`.
- `DimDate`: continuous calendar table related to event dates.

### Facts

- `FactLikes`: one row per `likes.id`.
- `FactComments`: one row per `comments.id`.
- `FactMedia`: one row per `media.id`.
- `FactFollows`: one row per `followers.id`.
- `FactBookmarks`: one row per `bookmarks.id`.
- `FactStatusHashtags`: one row per `status_hashtags.id`; use it as a bridge between statuses and hashtags.
- `FactNotifications` and `FactAccountLogs`: optional operational/event analytics from JSONL, with privacy minimization.

Relationships should generally be **one-to-many, single direction from dimensions to facts**. The `followers` table contains both the follower and followed profile roles, so use a role-playing `DimFollowedProfile` for `following_id` instead of a bidirectional many-to-many relationship. Use a separate `DimDate` relationship for each event fact's date, with inactive role-playing date relationships when you need multiple date roles.

Do not merge Likes, Comments and Media directly into one flattened status table. Multiple one-to-many joins will multiply rows and overcount events. For `statuses.likes_count`/`reply_count`, remember these are stored synthetic counters and are not guaranteed to reconcile to generated event rows.

## 7. Create the report in phases

1. **Core model:** DimProfile, DimStatus, DimHashtag, DimDate, FactLikes, FactComments, FactMedia and FactFollows.
2. **Content analytics:** post volume over time, event-derived engagement, post types and visibility; use `status_hashtags` for hashtag analysis.
3. **Operational analytics:** selected notifications/account log trends without exposing sensitive details.
4. **Quality page:** expected versus actual row counts, missing keys, duplicate keys, orphan relationships and refresh timestamp.

## 8. Refresh and portability

- Use **Home → Refresh** in Power BI Desktop after regenerating data.
- Keep `pLakehousePath` and the ODBC DSN database path aligned with the actual landing folder.
- For Power BI Service refresh with local files, plan for an on-premises data gateway and correctly configured file/ODBC dependencies; desktop refresh alone does not configure service refresh.
- Commit the generator, schema, M sources and documentation. Exclude the full synthetic landing zone, SQLite file and other generated outputs from Git unless the repository intentionally needs a compact sample.

## Troubleshooting

- **File not found:** check `pLakehousePath` and the exact subfolder/file name.
- **ODBC DSN not found:** create `PixelFedSQLite` in ODBC Data Sources (64-bit), not the 32-bit administrator.
- **SQLite driver mismatch:** install a driver with the same architecture as Power BI Desktop and confirm it can open `pixelfed_operational_tables.sqlite`.
- **JSON parse error:** use the supplied JSONL M query; do not pass the entire `.jsonl` file directly to `Json.Document` as one JSON document.
- **Wrong type or conversion error:** compare the column definition in `schema.md`; blank values in nullable numeric/time columns should remain null, not be replaced with invented zeros.
- **Relationship error:** check both the referenced column and relationship direction against `metadata\schema_contract.json`. Polymorphic fields such as `object_type` + `object_id` are not ordinary foreign keys on their own.
