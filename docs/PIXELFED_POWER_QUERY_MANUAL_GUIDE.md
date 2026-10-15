# PixelFed Analytics Engineering — Manual Power Query and Galaxy Model Guide

> **How to use this guide:** complete the steps yourself in Power BI Desktop. This is a documentation-only walkthrough: it contains no paste-ready M, SQL, DAX, TMDL, or automation scripts. It deliberately teaches the Power Query UI and explains when to work in the Advanced Editor without doing the implementation for you.

## Project target

- **Project:** `pixelfed-analytics-engineering`
- **Canonical schema:** `schema.md` — 54 MySQL tables, source column names, data types, keys, relationships, and indexes.
- **Landing directory:** `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`
- **Target outcome:** a manually built Power BI model with a schema-faithful staging layer, validated curated queries, and a galaxy (fact constellation) model.
- **Important boundary:** one source table is assigned to one physical format. Do not convert files to another format or create duplicate copies just to make Power BI import easier.

## Recommended learning sequence

1. Confirm the landing-zone files and their format assignment.
2. Create a new Power BI Desktop file and establish query organization.
3. Import one pilot table from each format.
4. Fix and validate SQLite ODBC integer fields before bulk loading.
5. Complete all 54 staging queries while preserving the source schema.
6. Profile and validate staging before building dimensions and facts.
7. Create curated dimensions and fact tables by referencing staging queries.
8. Create relationships manually in Model view.
9. Validate the galaxy and then design report pages.

Do not attempt to model all 54 tables at once. Prove one example from each source format first, write down what worked, and then repeat the pattern for the remaining tables.

---

## 1. Understand the landing zone before opening Power BI

### 1.1 Confirm the path

Open File Explorer and navigate to the landing directory above. If you extracted the dataset ZIP, make sure the archive's `landing` folder is inside the `data` folder only once. Avoid accidentally creating a repeated path such as `data\landing\landing`.

Look for the format folders and metadata folder. The exact folder names are documented in the project README and format catalog. The metadata directory should contain the manifest, row counts, and data-quality report from the generation run.

### 1.2 Know the one-format-per-table assignment

| Format | Number of tables | Tables assigned to this format |
|---|---:|---|
| Gzipped CSV (`.csv.gz`) | 11 | `statuses`, `likes`, `comments`, `media`, `followers`, `status_hashtags`, `mentions`, `story_views`, `hashtag_follows`, `reports`, `report_comments` |
| CSV (`.csv`) | 10 | `users`, `profiles`, `hashtags`, `bookmarks`, `collections`, `collection_items`, `circles`, `circle_profiles`, `avatars`, `stories` |
| JSON Lines (`.jsonl`) | 8 | `account_logs`, `activities`, `failed_jobs`, `jobs`, `mod_logs`, `notifications`, `report_logs`, `websockets_statistics_entries` |
| JSON array (`.json`) | 5 | `direct_messages`, `discover_category_hashtags`, `import_datas`, `import_jobs`, `profile_sponsors` |
| Excel workbook (`.xlsx`) | 7 | `discover_categories`, `instances`, `migrations`, `places`, `oauth_personal_access_clients`, `user_devices`, `user_settings` |
| SQLite (`.sqlite`) | 13 | `contacts`, `email_verifications`, `follow_requests`, `newsroom`, `oauth_access_tokens`, `oauth_auth_codes`, `oauth_clients`, `oauth_refresh_tokens`, `pages`, `password_resets`, `sessions`, `user_filters`, `user_invites` |
| **Total** | **54** | Every schema table is assigned once. |

Use the mapping above as the ingestion checklist. Do not import `statuses` from both the compressed CSV and another convenience copy. If a table's file is missing, troubleshoot the generator or extraction step rather than silently substituting a different format.

### 1.3 Keep the schema as the contract

Treat `schema.md` as the source contract, not as a promise that Power BI will automatically infer the correct types. The schema contains MySQL types, nullability assumptions, primary keys, selected foreign keys, relationships, and unique indexes. Some keys are strings even if their names end in `_id` (for example OAuth token IDs and session IDs). Do not convert every ID-like column to a number simply because its name contains `id`.

---

## 2. Create a clean Power BI working file

1. Open Power BI Desktop and create a new blank report.
2. Save it in your project under `powerbi` using a working name such as `PixelFedAnalytics_Dev`.
3. Use a development copy until the entire import and model have been validated.
4. Select **Home → Transform data** to open Power Query Editor.
5. In the Queries pane, create query groups using right-click → **New Group**. Use clear groups such as **00 Parameters**, **01 Staging - Files**, **02 Staging - ODBC**, **03 Curated Dimensions**, **04 Curated Facts and Bridges**, and **99 Data Quality**.
6. Use the naming pattern `stg_<schema_table>` for staging queries. Use `Dim...`, `Fact...`, or `Bridge...` only for curated tables. Keep names consistent with the source schema and project documentation.

### 2.1 Create the landing path parameter through the UI

1. In Power Query Editor, select **Home → Manage Parameters → New Parameter**.
2. Name it `pLakehousePath`.
3. Choose **Text** as the type.
4. Set the current value to your exact landing directory: `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`.
5. Move it into the **00 Parameters** group.

For file-based queries, Power Query's GUI initially writes the chosen file path into the query's source step. To make the project portable, use the Advanced Editor to replace that fixed path reference with the parameter reference. Do this carefully: change the path reference only, not the surrounding source or transformation logic. Refresh the preview after every edit.

### 2.2 Learn the two ways to work in Power Query

**GUI-first workflow:** create the query using **Home → New Source**, then perform transformations through ribbon commands. Power Query writes the M steps for you. This is the preferred starting point while learning.

**M-assisted workflow:** select a query and use **View → Formula Bar** to inspect a selected step. Use **View → Advanced Editor** only when a transformation cannot reasonably be built in the UI or when you need to parameterize a source path, parse compressed files, parse JSON Lines, or adjust an ODBC source projection. Read the generated M before editing it. Change one small section, select **Done**, inspect the preview, and confirm the new step in **Applied Steps**.

Do not replace an entire query with unfamiliar content. The safest learning pattern is: create one step in the UI, inspect the M it generated, understand the change, and only then edit a similar step manually.

---

## 3. Import one pilot table from every format

Import these pilot tables first. It provides a manageable test of each connector pattern before you expand to all 54 tables.

| Pilot | Format | What you are learning |
|---|---|---|
| `users` | CSV | Header promotion, column types, and safe removal of unnecessary columns in curated tables |
| `statuses` | Gzipped CSV | Binary decompression followed by delimited-text parsing |
| `account_logs` | JSON Lines | Parsing one JSON object per line |
| `direct_messages` | JSON array | Converting records and lists into a table |
| `places` | Excel | Selecting a worksheet/table from a workbook |
| `user_filters` | SQLite through ODBC | Relational navigation, source SQL projection, and integer type repair |

Name each pilot query with its staging prefix. For example, the source table `users` should become `stg_users`. Keep only one query per schema table in staging.

### 3.1 Ordinary CSV: use the UI first

1. Select **Home → New Source → Text/CSV**.
2. Navigate to the assigned `.csv` file for the pilot table.
3. Check that Power BI recognizes the delimiter, encoding, and first-row headers correctly.
4. Choose **Transform Data**, not **Load**, so you can inspect the data first.
5. Confirm that the first row became column headers exactly as shown in `schema.md`.
6. Rename the query in the Queries pane to `stg_<table>`.
7. Explicitly set data types at the end of your core staging transformations. Do not blindly accept every automatically generated type step without reviewing it.
8. Compare the visible column names and order with the schema contract.

Use the same process for the remaining plain CSV files.

### 3.2 Gzipped CSV: GUI plus deliberate M editing

A `.csv.gz` file is a compressed binary file, not an ordinary CSV file that can be opened directly as text. Use this format to practice the M source layer.

1. In Power Query Editor, choose **Home → New Source → Blank Query**.
2. Rename the query to its staging name, such as `stg_statuses`.
3. Open **View → Advanced Editor** and inspect the empty-query structure.
4. Build the source steps in this order: read the selected file as binary; decompress the binary with the GZip compression option; pass the decompressed content to the CSV parser; promote the first row to headers; then set explicit column types.
5. The relevant M concepts to learn are `File.Contents`, `Binary.Decompress`, `Compression.GZip`, `Csv.Document`, header promotion, and explicit type conversion. Learn each operation separately rather than pasting a full query you do not understand.
6. Use the parameter from section 2.1 for the path. Confirm that the source points to the `.csv.gz` file in the assigned format folder.
7. Compare all column names and order with `schema.md`; verify that row counts match the landing metadata.

Do not export the decompressed data to a new CSV or Parquet file just to get Power BI to read it. Decompression should happen inside the query so the assigned source format remains unchanged.

### 3.3 JSON Lines: parse every line as an individual record

The JSON Lines files contain one JSON object per line. They are not the same as a single JSON array, and loading a JSON Lines file directly through the standard JSON connector may produce a parsing error.

1. Create a **Blank Query** and name it for the assigned staging table.
2. Use the Advanced Editor to build a source step that reads the file as binary.
3. Split the binary into lines using the M function `Lines.FromBinary`, explicitly preserving UTF-8 text handling.
4. Remove blank or whitespace-only lines before parsing.
5. Apply `Json.Document` to each remaining line individually.
6. Turn the resulting records into a table and expand the fields that are consistently present.
7. If a column contains nested JSON, keep the payload intact during staging unless you have a specific analytics requirement to expand it. Expanding nested lists can create more rows and alter the table's grain.
8. Set types for stable columns such as IDs and timestamps only after confirming their actual values and format.

After the query works for `stg_account_logs`, repeat the same pattern for the other seven JSONL tables. Adjust your selected fields and types based on each table's source contract.

### 3.4 JSON array: use Navigator and expand deliberately

1. Select **Home → New Source → JSON** and choose the assigned `.json` file.
2. Review whether the first parsed value is a List or a Record. Do not assume all JSON files start in the same shape.
3. If the root is a list of records, use the UI's **To Table** action, then expand the record values into columns.
4. If the root is a record containing a nested list, navigate to the correct field and convert that list to a table.
5. Avoid expanding every nested field automatically. Preserve nested or semi-structured payloads in staging until you know how they should be modeled.
6. Rename the query and apply explicit types after inspecting the data.

The five `.json` files in this project are assigned sources. Do not replace them with a different file type.

### 3.5 Excel workbook: navigate to the correct worksheet

1. Select **Home → New Source → Excel workbook**.
2. Select the assigned `.xlsx` file.
3. In Navigator, choose the worksheet or table that holds the dataset, not the workbook object or a sheet-metadata record.
4. Select **Transform Data**.
5. Promote headers if Power Query has not done so already. Verify the header names and order against the schema.
6. Remove workbook-specific artifacts such as blank rows, repeated title lines, and unused columns only when those are not part of the table contract.
7. Set explicit types and rename the query to the source table's staging name.

### 3.6 SQLite through ODBC: first test the connection, then fix data types

1. Confirm the SQLite database file is present in the landing folder.
2. Open **ODBC Data Sources (64-bit)** from Windows Start.
3. Create or verify a User DSN named `PixelFedSQLite`, pointing at the SQLite file.
4. Make sure Power BI Desktop and the ODBC driver are both 64-bit.
5. In Power BI, choose **Home → New Source → ODBC**, select `PixelFedSQLite`, and open Navigator.
6. For an unaffected table, select the table and choose **Transform Data**. Verify columns and types before continuing.
7. For a table where integer columns arrive as Binary, use the ODBC connector's **Advanced options** and source SQL statement to select columns explicitly. In that source projection, return each affected numeric field as text while retaining the original column name. Do not use a wildcard projection for the corrected query, because you need control over the type of each selected field.
8. Back in Power Query, change the returned numeric text fields to Whole Number / 64-bit integer in a later type step. Confirm that nulls remain null and numeric values are unchanged.
9. Do not cast text keys such as OAuth token/auth-code IDs and session IDs to integers.
10. Apply this pattern to the affected SQLite tables listed in the ODBC section below, then refresh each query before continuing.

---

## 4. Repair ODBC integer fields returned as Binary

### 4.1 What the symptom means

If Power Query's source preview displays a numeric ID column as `Binary`, and changing its type to Whole Number fails, do not try to reinterpret the bytes as text or a number. In this project's SQLite source, the intended ID values are numeric; the failure is consistent with ODBC type metadata or driver behavior.

The fix belongs at the source projection: use the ODBC Advanced Options SQL statement to return affected integer fields as text, then convert that text to a numeric type inside Power Query. The cast must retain the original output field name so downstream joins are stable.

### 4.2 Affected tables and key columns

Use this checklist while fixing the SQLite imports. Some tables have additional integer flags that can be affected by the same driver behavior, so inspect all integer-typed fields in each query rather than only the key named in the first column.

| SQLite table | Columns to inspect carefully |
|---|---|
| `contacts` | `id`, `user_id`, `response_requested` |
| `email_verifications` | `id`, `user_id` |
| `follow_requests` | `id`, `follower_id`, `following_id`, `is_rejected`, `is_local` |
| `newsroom` | `id`, `user_id`, `force_modal`, `show_timeline`, `show_link`, `auth_only` |
| `oauth_access_tokens` | `user_id`, `client_id`, `revoked` |
| `oauth_auth_codes` | `user_id`, `client_id`, `revoked` |
| `oauth_clients` | `id`, `user_id`, `personal_access_client`, `password_client`, `revoked` |
| `oauth_refresh_tokens` | `revoked` |
| `pages` | `id`, `category_id`, `active`, `cached` |
| `sessions` | `user_id`, `last_activity` |
| `user_filters` | `id`, `user_id`, `filterable_id` |
| `user_invites` | `id`, `user_id`, `profile_id` |
| `password_resets` | No numeric ID fields in the documented table; verify its text and date fields instead. |

Some of these fields are flags or counters rather than keys. They are listed because the driver workaround covers the corresponding integer-typed columns, not because all of them are foreign keys.

### 4.3 Validate the ODBC repair one column at a time

1. Select the table in the Queries pane and inspect the earliest **Source** step.
2. Confirm the DSN points to the intended SQLite file, not an older copy.
3. Confirm that the source SQL explicitly selects the relevant columns.
4. For each integer column that appears as Binary, adjust only that column's source expression so SQLite returns text. Keep its output column name unchanged.
5. Apply the change and check the preview before changing any other fields.
6. Set the converted numeric text fields to the correct Power Query numeric type: Whole Number for IDs and flags; use the schema's actual type for counts and counters.
7. Check for conversion errors and null changes. An ID column defined as a string in the schema must remain text even if it looks numeric.
8. Refresh the query and confirm it can be used as a join key in a later query.

If `CAST(... AS TEXT)` still comes through as Binary in the preview, stop. Check the installed ODBC driver and DSN before attempting byte decoding. A compatible driver or a different supported SQLite access route may be required. Do not build relationships until the key types are stable.

---

## 5. Build the complete staging layer with Power Query best practices

After all six pilot queries work, repeat the same connector pattern for every assigned table. Use `schema.md` as the checklist.

### 5.1 Preserve the source contract in staging

For all `stg_` queries:

- Preserve the schema's column names and, where practical, column order.
- Keep the source keys and foreign-key columns needed for validation and later joins.
- Do not merge multiple source tables into a staging query just because they share columns.
- Do not deduplicate fact/event tables automatically. Duplicate-looking rows may be legitimate events, or they may be a quality issue that should be diagnosed rather than hidden.
- Do not replace nulls with zero or empty text without a documented business rule.
- Do not remove soft-delete fields such as `deleted_at` from staging; make inclusion/exclusion decisions in the curated layer.
- Preserve JSON payloads as text or structured records during staging. Expand only after deciding what their fields mean.
- Keep staging transformations predictable, testable, and close to the source contract.

### 5.2 Apply explicit data types at the end of the core staging steps

Review these common PixelFed patterns:

- Numeric primary/foreign keys such as `users.id`, `profiles.id`, `statuses.id`, and `user_filters.filterable_id`: Whole Number / 64-bit integer when the source field is numeric.
- Character keys such as `sessions.id`, `oauth_access_tokens.id`, and `oauth_auth_codes.id`: Text.
- Timestamps: Date/Time when the source represents a timestamp without timezone metadata. Confirm the generator's timestamp convention before converting time zones.
- Integer flags such as `is_nsfw`, `is_private`, `revoked`, `active`, and `deleted` indicators: retain Whole Number at the source-faithful stage; convert to True/False only when the domain is confirmed to be strictly 0 or 1 and the curated model benefits from Boolean semantics.
- Counters such as `likes_count`, `reblogs_count`, `reply_count`, `followers_count`, `size`, and `view_count`: use numeric types matching the intended range.
- JSON and long text fields: Text or structured values, depending on the source and required analysis. Do not let automatic detection expand or infer unstable schemas silently.
- Enum-like values such as `visibility`, `scope`, `status`, and `type`: Text in staging. Validate their distinct values before designing report categories.

Do not blanket-convert all names ending in `_id` to Whole Number. Check the schema type first.

### 5.3 Use data profiling before changing values

In Power Query Editor, go to **View** and enable **Column quality**, **Column distribution**, and **Column profile**. By default, profiling may be based on the first 1,000 rows. When checking a full landing table, change the profiling scope to the entire dataset where practical.

For every key column, inspect empty values, errors, distinct count, and unique count. For status and activity values, inspect distributions for unexpected spelling, casing, or unexpected categories. For timestamps, look for parse failures and dates outside the synthetic reference range.

Keep an explicit quality query or notes for issues you find. Do not repair a data-quality issue by hiding it with Remove Errors unless you have identified and documented why each affected row should be excluded.

### 5.4 Filter and remove columns at the right time

- For a file source, keep only the columns needed for the staging contract, then keep a full schema-faithful staging query if your project requires exact raw-schema validation.
- For ODBC, avoid `SELECT *` in the manually corrected query. Select explicit columns and cast only affected fields at the source.
- Filter irrelevant rows early when you have a clear business rule, but do not apply report-specific filters to shared staging queries.
- Perform expensive merges, grouping, sorting, and nested expansion late unless they are required for parsing or validation.
- For ODBC, check whether a transformation can fold to the source; do not assume every transform folds, especially after native SQL has been specified.
- For local files, expect parsing and most transformations to run in Power Query rather than in the file source.

### 5.5 Organize queries so another analyst can maintain them

- Use the query groups created in section 2.
- Rename the autogenerated Applied Steps with meaningful labels, such as “Read workbook”, “Promoted headers”, “Cast numeric identifiers”, or “Validated timestamps”.
- Add query descriptions using Query Properties where available. State source format, source table, grain, any important assumptions, and whether the query is staging or curated.
- Use **View → Query Dependencies** to review the source-to-curated flow. Staging should be the base; dimensions and facts should reference staging rather than re-importing the same physical file independently.
- Use **Refresh Preview** while building one table at a time. Avoid repeatedly refreshing all 54 queries during early development.
- Once curated tables are ready, right-click staging queries and clear **Enable load** so raw staging tables do not clutter the semantic model. Keep them available for query references and refresh as required.

---

## 6. Turn staging into a galaxy model using references, not duplicate imports

The landing schema is operational and normalized. The report model should be a separate layer of curated tables built by referencing staging queries.

### 6.1 Create curated queries through the GUI

For each curated table below:

1. Right-click the relevant `stg_` query and select **Reference**. Do not create a second source connection.
2. Rename the new query to the curated name.
3. Use **Choose Columns** to keep only the fields needed for analytics.
4. Use **Rename** for clear model-facing names. Retain source table/key names in staging so traceability is not lost.
5. Set curated column types, resolve nullability and key checks, then document the grain in the query description.
6. Leave the new curated query enabled for load; disable load for intermediate staging queries after validation.

When you need a second role for the same entity, create another reference to the curated dimension and name its role clearly. Do not create multiple independent sources for the same table.

### 6.2 Start with the core dimensions

| Curated table | Source | Grain / unique key | Keep for reporting |
|---|---|---|---|
| `DimUser` | `stg_users` | One row per `users.id` | User key, account status, language, created date, selected non-sensitive account flags |
| `DimProfile` | `stg_profiles` | One row per `profiles.id` | Profile key, associated user key, username, status, public visibility/location attributes when appropriate, created date |
| `DimStatus` | `stg_statuses` | One row per `statuses.id` | Status key, author profile key, type, visibility, scope, language, NSFW flag, created date, place key |
| `DimHashtag` | `stg_hashtags` | One row per `hashtags.id` | Hashtag key, name, slug, NSFW/banned flags |
| `DimPlace` | `stg_places` | One row per `places.id` | Place key, place name, country, optional location attributes |
| `DimStory` | `stg_stories` | One row per `stories.id` | Story key, owning profile, type, created date, expiry date, visibility attributes |
| `DimDate` | Created manually in Power Query | One row per calendar date | Date key, date, year, quarter, month number/name, year-month attributes |

For `DimDate`, use a new Blank Query and learn to construct the calendar through Power Query's list-generation and date functions in the Advanced Editor. Base its start and end on an explicit reporting range or the validated minimum and maximum event dates. Do not infer the date range from a small preview only. This guide intentionally leaves the M expression for you to write manually.

Keep secrets out of curated dimensions. Never bring `password`, `remember_token`, `2fa_secret`, `2fa_backup_codes`, `private_key`, OAuth `secret`, reset tokens, session `payload`, IP address, user-agent, device fingerprint, and other unneeded account/security fields into report-facing queries. Synthetic data is still a chance to practice least-privilege modeling.

### 6.3 Create the event facts at their natural grain

| Curated table | Source | Grain | Main relationships |
|---|---|---|---|
| `FactPostMetrics` | `stg_statuses` | One row per status; stored counters only once | Status, author/profile, date, place |
| `FactLikes` | `stg_likes` | One row per like event | Status, liker profile, author role, event date |
| `FactComments` | `stg_comments` | One row per comment | Status, commenter profile, author role, event date |
| `FactMedia` | `stg_media` | One row per media item | Status, owner profile, uploader user where valid, event date |
| `FactFollows` | `stg_followers` | One row per directed follow row | Follower profile, followed profile, follow date |
| `FactBookmarks` | `stg_bookmarks` | One row per bookmark | Status, bookmarking profile, event date |
| `BridgeStatusHashtag` | `stg_status_hashtags` | One row per status-hashtag association | Status, hashtag, profile only when valid |
| `FactMentions` | `stg_mentions` | One row per mention record | Status, mentioned profile, event date |
| `FactStoryViews` | `stg_story_views` | One row per story-view event | Story, viewer profile, event date |
| `FactNotifications` | `stg_notifications` | One row per notification | Recipient profile, actor profile, event date and read date where needed |
| `FactAccountLogs` | `stg_account_logs` | One row per account log | User, event date; exclude IP/user agent in curated output |
| `FactWebSocketUsage` | `stg_websockets_statistics_entries` | One row per statistics record | Date plus numeric message/connection metrics |

Do not merge `likes`, `comments`, and `media` into `statuses`. One status may have many events of each kind. Expanding these relationships into one wide table multiplies rows and inflates measures. Also keep the stored counters in `FactPostMetrics` distinct from event-derived counts: the synthetic source may intentionally generate those independently.

### 6.4 Handle JSON and polymorphic relationships cautiously

Some fields are intentionally flexible:

- `collection_items.object_type` plus `object_id` can reference different object types. Do not make a single relationship from `object_id` to multiple target tables. Create type-specific curated paths only after you filter each object type.
- `user_filters.filterable_type` plus `filterable_id` is polymorphic. Do not relate `filterable_id` to one entity table without checking `filterable_type`.
- `notifications.item_type` plus `item_id`, and `reports.object_type` plus `object_id`, have the same issue. Preserve them in staging; model the object link only for a validated type-specific scenario.
- JSON payloads such as activity data, metadata, sponsor details, and message payloads should not be expanded automatically. Choose fields based on a reporting question and define how nested arrays affect row grain.

### 6.5 Check the schema's unusual relationship declarations

The schema document includes the relationship `followers.id` to `follow_requests.follower_id`, which is unusual for the semantic meaning of a follow request. It also lists `followers.following_id` as a column without an explicit foreign-key declaration. Treat these as validation items, not relationships to create blindly.

For the galaxy, the intended meanings are typically `followers.profile_id` as the follower and `followers.following_id` as the followed profile. Before relating both ends to `DimProfile`, confirm each key exists in the profile dimension and verify the generated source's semantics. Document any deviation from the source schema rather than silently correcting it.

The `users` and `profiles` tables also contain links in both directions in the schema. Avoid creating two active model relationships that form a cycle. Inspect which user/profile key is populated, decide the intended reporting navigation, and use one clear active path.

---

## 7. Create relationships manually in Model view

Only create relationships after the curated queries have loaded and their keys are valid.

1. Switch to **Model view**.
2. Use **Manage relationships → New**, or drag a validated dimension key onto its corresponding fact foreign key.
3. For standard dimension-to-fact links, use **One-to-many (1:*)**, with the dimension on the one side.
4. Use **Single** cross-filter direction from the dimension to the fact as the default.
5. Keep relationships active only where the filter path is unambiguous. Create role-playing dimensions when the same entity has different business meanings, such as follower and followed profile, author and actor, or notification recipient and actor.
6. Confirm Power BI has not guessed a many-to-many or many-to-one relationship in the wrong direction.
7. Do not create direct relationships between facts. Shared dimensions and bridge tables should express analysis across facts.
8. For date fields, start with one active created-date relationship per fact. For a second date role, use a deliberate role-playing date table or a carefully documented inactive relationship strategy; do not leave multiple ambiguous active date paths.
9. Hide technical keys from the report field list only after relationship creation and validation.

### 7.1 Suggested first relationship set

Create only the following core relationships first, then add the others after the pilot model works:

- `DimProfile` to `FactLikes` by the like actor/liker profile key.
- `DimProfile` to `FactComments` by the commenter profile key.
- `DimProfile` to `FactMedia` by the media owner's profile key.
- `DimProfile` to `FactBookmarks` by the bookmarking profile key.
- `DimStatus` to `FactLikes`, `FactComments`, `FactMedia`, `FactBookmarks`, `FactMentions`, and `BridgeStatusHashtag` by status key.
- `DimHashtag` to `BridgeStatusHashtag` by hashtag key.
- `DimStory` to `FactStoryViews` by story key.
- A follower-role profile dimension to `FactFollows` by follower profile key, and a followed-role profile dimension by the followed profile key.
- `DimDate` to each fact's chosen event-date key.
- `DimUser` to account-level facts only where the user key is valid and needed.

If the two sides of a relationship contain null keys, allow nulls on the many side where the source contract permits them. Nulls should not become artificial zero IDs.

---

## 8. Validation gates — do not move forward until these pass

### Gate A: source and parser validation

- [ ] All 54 assigned source tables have a staging query.
- [ ] Each table is imported from its assigned format only.
- [ ] No table was duplicated in another format to avoid learning its original format.
- [ ] Every query has the correct column names and the expected source order.
- [ ] GZip sources decompress inside Power Query; no alternate file was exported for convenience.
- [ ] JSON Lines records parse one line at a time.
- [ ] Excel queries navigate to a worksheet/table, not workbook metadata.
- [ ] SQLite ODBC reads from the intended DSN and file.

### Gate B: data types and quality

- [ ] Numeric identifiers are typed as Whole Number only when the schema defines them as numeric.
- [ ] Text identifiers remain text.
- [ ] The ODBC-affected fields no longer show Binary in the post-source preview.
- [ ] The ODBC cast fields convert to numeric values without errors or changed values.
- [ ] Timestamp parsing is consistent and the time convention is documented.
- [ ] Primary keys have no blanks and no duplicates.
- [ ] Foreign-key violations are investigated before relationships are created.
- [ ] Nulls and soft deletes are preserved until a business rule says how to handle them.
- [ ] Row counts match the landing metadata.

### Gate C: model validity

- [ ] Each dimension has a unique key.
- [ ] Every fact has a documented grain and one intended row meaning.
- [ ] There are no accidental fact-to-fact relationships.
- [ ] Relationships have the expected cardinality and filter direction.
- [ ] Role-playing dimensions prevent ambiguous actor/owner/follower paths.
- [ ] The profile/user link does not form a circular active path.
- [ ] The followers/follow_requests declaration has been validated rather than assumed.
- [ ] Security and token data is excluded from report-facing queries.

### Use Power Query's profiling and diagnostics deliberately

Enable column quality, distribution, and profile while authoring. If a query is unexpectedly slow, inspect **Tools → Query Diagnostics** for a focused step or refresh. Use diagnostics to learn whether the time is spent reading the source, parsing, or applying transformations; do not add speculative optimizations before you know the bottleneck.

---

## 9. Refresh and performance workflow

1. During development, refresh preview for the current query instead of refreshing every table after each small edit.
2. Validate the pilot tables before importing the remaining format assignments.
3. Keep explicit source projections for ODBC tables, particularly those with binary-mapped integers.
4. Filter early only when the filter is part of the reusable staging contract. Keep report-specific filters in curated queries or visuals.
5. Delay costly joins, groupings, sorts, and expansion until needed. Don't sort a table merely to make its preview look tidy; model relationships do not depend on source row order.
6. Monitor query folding for ODBC transformations where the connector supports it. For local CSV, GZip, JSON, JSONL, and Excel files, plan on Power Query processing the data locally.
7. Keep the model lean: disable staging load after validation, exclude unused long text and secret-like columns from curated queries, and avoid importing fields no report or audit needs.
8. When the full model is stable, use **Close & Apply**, save the PBIX, refresh, and verify the report totals. Keep a development copy for experiments.

---

## 10. Practical report build order

Build one report page only after the corresponding model checks pass.

### Page 1 — Content and engagement overview

Use post counts from the one-row-per-status fact, like and comment event counts from their event facts, and stored counters as separate measures. Add created-date trend analysis and breakdowns by status type, visibility, language, or NSFW flag where appropriate.

### Page 2 — Media and creator performance

Use profile and author-role dimensions to compare posts and media. Check that every visual uses the intended fact grain and that likes/comments/media are not joined together in Power Query.

### Page 3 — Social graph

Analyze follower and followed profile roles separately. Include validation for missing followed-profile keys before interpreting results as complete.

### Page 4 — Hashtag and discovery

Use `BridgeStatusHashtag` for status-to-hashtag associations. Analyze discovery category/hashtag data only after creating an explicit type-safe bridge, and don't join polymorphic object IDs indiscriminately.

### Page 5 — Data quality and pipeline health

Report source row counts, invalid/duplicate key counts, null key counts, type conversion errors, unresolved foreign keys, and refresh results. Keep the checks visible so the project demonstrates engineering controls—not only charts.

---

## 11. Troubleshooting guide

| Symptom | What to check first | Preferred response |
|---|---|---|
| CSV columns shift or appear in one column | Delimiter, encoding, header promotion | Fix the parser options in the source query; do not rename corrupted values manually. |
| GZip file appears as unreadable binary | Compression step is missing or source file is not the assigned file | Review the Binary source → GZip decompression → CSV parsing sequence. |
| JSON connector rejects a file | It may be JSON Lines rather than a single JSON document | Parse one line at a time; don't treat JSONL as a JSON array. |
| Nested JSON expansion multiplies rows | A list field is being expanded into multiple records | Keep it nested in staging or create a separate child/bridge table with a declared grain. |
| ODBC ID shows Binary | Driver metadata or source projection | Cast the affected numeric field to text in the source SQL, then type it as Whole Number in a later Power Query step. |
| ODBC key is text even though it looks numeric | It may be a genuine character identifier | Check `schema.md`; preserve text keys as text. |
| Relationship becomes many-to-many | Dimension key is not unique or types do not match | Fix duplicates/keys at the dimension layer; don't mask it with many-to-many. |
| Fact measures are inflated | Multiple one-to-many tables were merged before aggregation | Restore separate fact grains; analyze through shared dimensions. |
| Refresh is slow | Too many columns, early expensive steps, parsing, source read, or lack of folding | Profile first; remove unnecessary columns early and use Query Diagnostics when needed. |
| Date slicer misses some records | A timestamp was not reduced to the same date granularity as `DimDate` | Add a dedicated date-only column and relate it to the date dimension; retain original timestamps in staging. |

---

## 12. Completion definition

The project is ready for presentation when you can demonstrate, manually and confidently, that:

- you can explain why every one of the 54 tables is assigned to its particular format;
- you can import plain CSV and Excel from the UI, and explain the extra parsing required for GZip and JSON Lines;
- you understand why the SQLite ODBC workaround casts numeric fields to text before Power Query sets their final numeric types;
- the staging layer follows the source contract and has explicit, validated types;
- each curated fact has a declared grain and each dimension has a unique key;
- the galaxy shares conformed dimensions without accidental fact-to-fact joins;
- the report excludes credential-like fields and unnecessary personal data; and
- refresh and data-quality checks are documented.

## Official references

- [Microsoft Learn — Best practices when working with Power Query](https://learn.microsoft.com/en-us/power-query/best-practices)
- [Microsoft Learn — Understand star schema and the importance for Power BI](https://learn.microsoft.com/power-bi/guidance/star-schema)
- [Microsoft Learn — Understand query evaluation and query folding](https://learn.microsoft.com/en-us/power-query/power-query-folding)
- [Microsoft Learn — Query folding guidance in Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/guidance/power-query-folding)
- [Microsoft Learn — Power Query ODBC connector](https://learn.microsoft.com/en-us/power-query/connectors/odbc)
- [Microsoft Learn — Power Query JSON connector and JSON Lines limitation](https://learn.microsoft.com/en-us/power-query/connectors/json)
- [Microsoft Learn — Data profiling tools](https://learn.microsoft.com/en-us/power-query/data-profiling-tools)
- [Microsoft Learn — Query Diagnostics](https://learn.microsoft.com/en-us/power-query/query-diagnostics)
