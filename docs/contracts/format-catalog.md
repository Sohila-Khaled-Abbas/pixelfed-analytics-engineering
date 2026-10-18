# Format Catalog

This is an intentional polyglot landing zone for learning Power BI ingestion from multiple native source formats. The generator assigns one format to every schema table and writes from generated in-memory rows directly. It never converts a `.csv.gz` export to another format.

| Format | Table count | How Power BI reads it | Purpose |
|---|---:|---|---|
| Compressed CSV (`.csv.gz`) | 11 | GZip decompression → CSV parser | Large batch/event fact extracts; Power Query decompresses then parses CSV. |

| CSV (`.csv`) | 10 | CSV parser | Tabular source files with explicit header promotion and data-type conversion. |

| JSON Lines (`.jsonl`) | 8 | Split lines → JSON parse per line | Event/audit logs where each line is a standalone JSON record. |

| JSON array (`.json`) | 5 | JSON document → records table | Small semi-structured sources; one JSON document containing a list of records. |

| Excel workbook (`.xlsx`) | 7 | Excel.Workbook → worksheet table | Small reference and business extract tables; one table per workbook and sheet. |

| SQLite (`.sqlite`) | 13 | Odbc.Query against SQLite DSN | Relational operational/configuration tables accessed via a 64-bit ODBC DSN. |

## Compressed CSV (`.csv.gz`)

`statuses`, `likes`, `comments`, `media`, `followers`, `status_hashtags`, `mentions`, `story_views`, `hashtag_follows`, `reports`, `report_comments`

## CSV (`.csv`)

`users`, `profiles`, `hashtags`, `bookmarks`, `collections`, `collection_items`, `circles`, `circle_profiles`, `avatars`, `stories`

## JSON Lines (`.jsonl`)

`account_logs`, `activities`, `failed_jobs`, `jobs`, `mod_logs`, `notifications`, `report_logs`, `websockets_statistics_entries`

## JSON array (`.json`)

`direct_messages`, `discover_category_hashtags`, `import_datas`, `import_jobs`, `profile_sponsors`

## Excel workbook (`.xlsx`)

`discover_categories`, `instances`, `migrations`, `places`, `oauth_personal_access_clients`, `user_devices`, `user_settings`

## SQLite (`.sqlite`)

`contacts`, `email_verifications`, `follow_requests`, `newsroom`, `oauth_access_tokens`, `oauth_auth_codes`, `oauth_clients`, `oauth_refresh_tokens`, `pages`, `password_resets`, `sessions`, `user_filters`, `user_invites`

## Why these formats?

- **CSV and CSV.GZ** teach classic delimited-file ingestion and compressed batch landing.
- **JSON and JSONL** teach document-shaped data versus line-delimited events.
- **XLSX** represents spreadsheet-based business/reference extracts.
- **SQLite** provides a relational source to query using ODBC.

**Important:** Parquet and Feather are not emitted by this build because the execution environment used to create the downloadable dataset does not have PyArrow installed. They are not faked, renamed, or created from the CSV.GZ exports. The current repository still gives you six real, inspectable formats. A Parquet/Feather extension should assign additional source tables to those formats and generate them directly from the in-memory rows once PyArrow is installed; never duplicate a table simply to demonstrate a connector.