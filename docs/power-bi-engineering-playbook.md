# PixelFed Power BI Engineering Playbook

A GUI-first, code-aware guide for building a reliable Power BI model from this repository's existing synthetic PixelFed landing zone. It covers source connection, Power Query UI and M, dimensional modeling, DAX, report design, validation, performance, security, and delivery.

> **Data safety:** the expected local source is `D:\\courses\\Data Analysis 26-27\\Projects\\PixelFed\\data\\landing`. This guide reads the existing landing data. Do not rerun `src/generate_landing.py` against that folder unless you intentionally want to replace generator-owned tables and metadata. The data is synthetic and PixelFed-inspired, not real user data.

## 1. Target architecture and engineering contracts

Use a layered design with explicit ownership:

1. **Landing / Bronze** — generated source-like tables in their assigned native formats under `data/landing`. Treat the files as immutable inputs during BI development.
2. **Staging / Silver** — `stg_*` Power Query queries that preserve source grain and column meaning while applying technical types and repeatable normalization.
3. **Curated / Gold** — `Dim*`, `Fact*`, and `Bridge*` queries designed around documented business grains.
4. **Semantic model** — relationships, explicit DAX measures, format strings, hierarchies, hidden technical columns, and security.
5. **Report / delivery** — accessible pages, clear metric definitions, refresh checks, and a versioned PBIP/TMDL workflow where supported.

### Core engineering rules

- Preserve one physical source representation per source table. Do not create format conversions just to make ingestion feel uniform.
- Keep staging queries source-faithful. Create Reference queries for curated transformations rather than layering report logic into `stg_*`.
- Define and test the grain of every fact before adding relationships.
- Do not flatten independent one-to-many processes (posts, likes, comments, media, follows) into one table. That creates fan-out and inflated metrics.
- Use dimensions to filter facts; default to active, one-to-many, single-direction relationships.
- Prefer explicit measures over implicit sums. Give each measure a business definition and format.
- Never load passwords, OAuth tokens, session payloads, reset tokens, private message bodies, or unnecessary personal data into the report-facing model.
- Keep query steps deterministic and document assumptions about soft deletes, nulls, timestamps, and source counters.

## 2. Prepare Power BI Desktop safely

1. Confirm the expected landing directory exists in File Explorer and contains `metadata/manifest.json`, `metadata/row_counts.csv`, the assigned format folders, and `sqlite/pixelfed_operational_tables.sqlite`.
2. Run the repository validation script before modeling:

   ```powershell
   Set-Location "D:\\courses\\Data Analysis 26-27\\Projects\\PixelFed"
   python .\\src\\validate_landing.py --landing .\\data\\landing
   ```

3. Open Power BI Desktop and save the report inside the repository's `powerbi/` directory (or open the existing PBIP project if your local checkout contains it).
4. In **File → Options and settings → Options**, review data-load, privacy, and background preview settings. Keep privacy levels appropriate to the source; do not disable privacy protections as a generic performance fix.
5. If using SQLite queries, install a 64-bit SQLite ODBC driver matching Power BI Desktop's bitness and configure the `PixelFedSQLite` User DSN to point at the existing database. Test the DSN before loading all SQLite tables.
6. Use a parameter for the landing path if the queries in your local report support it. Keep the default pointed at the actual local `data\\landing` folder. Avoid hard-coding multiple different roots across queries.

### Recommended query groups

Create these groups in the Power Query Queries pane:

- `01 - Parameters`
- `02 - Staging`
- `03 - Data Quality`
- `04 - Dimensions`
- `05 - Facts and Bridges`
- `90 - Measures / Model Notes` (documentation only; measures live in the semantic model)
- `99 - Scratch`

Use consistent prefixes: `stg_`, `qa_`, `Dim`, `Fact` or `fct_`, and `Bridge`. Pick one fact naming convention and use it consistently across the model.

## 3. Power Query GUI workflow

### 3.1 Import and preserve each format

Use **Home → Get data** and choose the connector that matches the file. For local files, navigate to the appropriate subfolder and select the intended table file.

- CSV: choose **Text/CSV**, confirm delimiter and encoding, then **Transform Data**.
- Gzipped CSV: Power Query Desktop may not expose a reliable direct CSV.GZ connector in every build. Use the repository's existing M query if it already handles decompression, or decompress to a temporary working copy outside the canonical landing zone only when necessary. Do not replace the canonical `.csv.gz` source with a duplicate export.
- JSON array: choose **JSON**, then use **To Table** and expand records deliberately. Confirm field names and null handling.
- JSON Lines: treat each non-empty line as a JSON record. If the built-in UI connector does not parse the file as JSONL, use the existing M query pattern in this repository or a documented line-by-line parser.
- XLSX: use **Excel workbook**, select the intended sheet, and promote headers only if the connector has not already done so.
- SQLite: use the configured ODBC DSN and select the expected tables. Validate column types after import.

For every imported source, rename the query to `stg_<source_table>`. Preserve source column names in staging unless a documented connector limitation forces a change. Keep a short description of the source path, expected grain, and key.

### 3.2 Set types intentionally

In Power Query, select key columns and use **Transform → Data Type**. Confirm types for:

- identifiers: whole number or text according to the source contract; do not convert identifiers to floating point;
- timestamps: Date/Time or Date/Time/Timezone where the source semantics support it;
- flags: logical only when source values are genuinely Boolean;
- counters: whole number, with null policy documented;
- URLs and handles: text;
- nested JSON fields: expand only fields required by the analytical use case.

Avoid blindly using **Detect Data Type** across every table. Inspect conversion errors in a separate QA query before deciding whether to replace errors, retain nulls, or reject rows.

### 3.3 Profile data and create QA queries

Enable **View → Column quality**, **Column distribution**, and **Column profile**. Change profiling from the top 1,000 rows to the entire dataset before final sign-off.

For each key:
1. Right-click the staging query → **Reference**.
2. Rename the reference to a `qa_*` query.
3. Keep only the key column(s).
4. Use **Group By** and count rows.
5. Filter count greater than one to identify duplicate keys.

Repeat with anti-joins for foreign-key checks: select the child query, use **Merge Queries** with the parent key, choose a **Left Anti** join, and inspect any rows returned. A non-empty result indicates unresolved orphan records, unless the relationship is explicitly optional by contract.

Keep QA queries available during development. Disable load for QA queries after review to avoid cluttering the semantic model.

### 3.4 Reusable M patterns

Use **Home → Advanced Editor** to inspect or author M. These examples are patterns; align the query names and column names with the exact source schema in your local data.

**Reference an existing staging query and select required columns:**

```powerquery
let
    Source = stg_profiles,
    Selected = Table.SelectColumns(
        Source,
        {"id", "user_id", "username", "name", "created_at", "updated_at", "is_private"},
        MissingField.UseNull
    )
in
    Selected
```

**Apply explicit types and preserve conversion failures for QA:**

```powerquery
let
    Source = stg_profiles,
    Typed = Table.TransformColumnTypes(
        Source,
        {
            {"id", Int64.Type},
            {"user_id", Int64.Type},
            {"username", type text},
            {"name", type text},
            {"created_at", type datetime},
            {"updated_at", type datetime}
        },
        "en-US"
    )
in
    Typed
```

If timestamps include UTC offsets, do not cast them to local `datetime` until you have deliberately decided how to normalize time zones.

**Create a reusable duplicate-key QA query:**

```powerquery
let
    Source = stg_profiles,
    KeysOnly = Table.SelectColumns(Source, {"id"}),
    Grouped = Table.Group(
        KeysOnly,
        {"id"},
        {{"RowCount", each Table.RowCount(_), Int64.Type}}
    ),
    Duplicates = Table.SelectRows(Grouped, each [RowCount] > 1)
in
    Duplicates
```

**Add a reporting date without changing the source timestamp:**

```powerquery
let
    Source = stg_statuses,
    AddedDate = Table.AddColumn(
        Source,
        "CreatedDate",
        each try Date.From([created_at]) otherwise null,
        type date
    )
in
    AddedDate
```

Keep original source timestamps and add normalized/reporting columns as separate fields when both meanings are needed. Avoid blanket `try ... otherwise null` transformations that silently hide widespread data errors; pair them with QA counts.

## 4. Build the curated galaxy

Start with the core product processes. Expand to moderation, security, and operational telemetry only after the core model validates.

| Table | Grain (one row per) | Main source | Notes |
|---|---|---|---|
| `DimDate` | calendar date | derived from fact date range | Mark as date table |
| `DimTime` | time-of-day second or minute, depending on reporting needs | derived | Optional if time-of-day analysis is required |
| `DimProfile` | profile ID | `stg_profiles` | Keep public/profile attributes only |
| `DimUser` | user/account ID | `stg_users` | Do not expose credentials or secrets |
| `DimInstance` | instance ID | `stg_instances` | Local/federated instance context |
| `DimStatus` | status/post ID | `stg_statuses` | Visibility, content type, creation date |
| `DimHashtag` | hashtag ID | `stg_hashtags` | Use bridge for many-to-many tags |
| `FactPosts` | one row per status | `stg_statuses` | One post-level record |
| `FactLikes` | one row per like event | `stg_likes` | One interaction per source event |
| `FactComments` | one row per comment | `stg_comments` | Preserve comment grain |
| `FactMedia` | one row per media item | `stg_media` | A post can have multiple media rows |
| `FactFollows` | one row per directed follow edge | `stg_followers` | Follower and followed are separate roles |
| `FactStoryViews` | one row per story-view event | `stg_story_views` | Viewer and story owner have separate roles |
| `BridgeStatusHashtag` | one post–hashtag association | `stg_status_hashtags` | Define duplicate-pair handling |

### Build dimensions through Reference

In the Queries pane, right-click `stg_profiles` → **Reference** → rename to `DimProfile`. Choose the attributes needed for analysis, enforce key type, check one row per profile ID, and sort only when required for presentation. Do not use Remove Duplicates to conceal conflicting profile records without investigating why they differ.

Repeat for other dimensions. For a role such as follower/followed profile, reuse `DimProfile` through role-playing dimension queries only when the report needs independent slicers for each role. Keep relationship paths unambiguous.

### Facts: preserve the grain

For `FactLikes`, reference `stg_likes`, keep the event ID, profile ID, status ID, timestamp, and the minimum audit columns required by definitions. Apply the agreed deleted-record policy. Do not merge post, comment, and media rows into this table.

For `FactPosts`, use one row per status. Stored counters such as `likes_count` are snapshots/attributes of the source record; they are not interchangeable with a count of rows in `FactLikes`. Label the difference clearly in measure names.

For `BridgeStatusHashtag`, validate the intended uniqueness of the status/hashtag pair. If the source has duplicate associations, flag them in QA before applying a documented deduplication rule.

### Dynamic DimDate in M

Create a **Blank Query**, rename it `DimDate`, open **Advanced Editor**, and use the following. It derives the range from `FactPosts[created_at]`; change the column/query if your curated table uses a different name.

```powerquery
let
    Dates =
        List.RemoveNulls(
            List.Transform(
                FactPosts[created_at],
                each try Date.From(_) otherwise null
            )
        ),
    MinDate = if List.IsEmpty(Dates) then #date(2020, 1, 1) else List.Min(Dates),
    MaxDate = if List.IsEmpty(Dates) then #date(2020, 12, 31) else List.Max(Dates),
    DayCount = Duration.Days(MaxDate - MinDate) + 1,
    DateList = List.Dates(MinDate, DayCount, #duration(1, 0, 0, 0)),
    AsTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    Typed = Table.TransformColumnTypes(AsTable, {{"Date", type date}}),
    AddDateKey = Table.AddColumn(Typed, "DateKey", each Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]), Int64.Type),
    AddYear = Table.AddColumn(AddDateKey, "Year", each Date.Year([Date]), Int64.Type),
    AddQuarter = Table.AddColumn(AddYear, "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    AddMonthNumber = Table.AddColumn(AddQuarter, "MonthNumber", each Date.Month([Date]), Int64.Type),
    AddMonth = Table.AddColumn(AddMonthNumber, "Month", each Date.ToText([Date], "MMMM", "en-US"), type text),
    AddYearMonth = Table.AddColumn(AddMonth, "YearMonth", each Date.ToText([Date], "yyyy-MM", "en-US"), type text),
    AddWeekdayNumber = Table.AddColumn(AddYearMonth, "WeekdayNumber", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    AddWeekday = Table.AddColumn(AddWeekdayNumber, "Weekday", each Date.ToText([Date], "dddd", "en-US"), type text),
    AddWeekend = Table.AddColumn(AddWeekday, "IsWeekend", each [WeekdayNumber] >= 6, type logical)
in
    AddWeekend
```

Sort `Month` by `MonthNumber` and `Weekday` by `WeekdayNumber` in Model/Data view. In **Table tools → Mark as date table**, select `DimDate[Date]`. The date column must be unique, non-null, and contiguous. If the model includes future-dated events, include them intentionally rather than clipping to today's date.

### Dynamic DimTime in M

For time-of-day reporting, use a second blank query named `DimTime`. This example creates one row per second (86,400 rows). If second-level precision is not needed, use minute-level grain (1,440 rows) instead.

```powerquery
let
    Seconds = List.Numbers(0, 86400),
    AsTable = Table.FromList(Seconds, Splitter.SplitByNothing(), {"SecondOfDay"}),
    Typed = Table.TransformColumnTypes(AsTable, {{"SecondOfDay", Int64.Type}}),
    AddTime = Table.AddColumn(Typed, "Time", each #time(
        Number.IntegerDivide([SecondOfDay], 3600),
        Number.IntegerDivide(Number.Mod([SecondOfDay], 3600), 60),
        Number.Mod([SecondOfDay], 60)
    ), type time),
    AddHour = Table.AddColumn(AddTime, "Hour", each Number.IntegerDivide([SecondOfDay], 3600), Int64.Type),
    AddMinute = Table.AddColumn(AddHour, "Minute", each Number.IntegerDivide(Number.Mod([SecondOfDay], 3600), 60), Int64.Type),
    AddSecond = Table.AddColumn(AddMinute, "Second", each Number.Mod([SecondOfDay], 60), Int64.Type),
    AddHourLabel = Table.AddColumn(AddSecond, "HourLabel", each Text.PadStart(Text.From([Hour]), 2, "0") & ":00", type text),
    AddPeriod = Table.AddColumn(AddHourLabel, "DayPeriod", each if [Hour] < 6 then "Night" else if [Hour] < 12 then "Morning" else if [Hour] < 18 then "Afternoon" else "Evening", type text)
in
    AddPeriod
```

Add a `TimeKey` only if the chosen model needs an integer relationship key; for second-level grain, `SecondOfDay` is already unique. In each fact, derive the same key from its event timestamp. Do not relate a DateTime column directly to a time-only dimension.

### Date-role guidance

A fact can have multiple timestamps (created, updated, deleted, ingested). Use one active date relationship per fact for the primary reporting date. For additional date roles, use inactive relationships with `USERELATIONSHIP` measures or duplicate the date dimension for role-playing when users need independent simultaneous date slicers. Document the chosen default.

## 5. Configure the semantic model

In **Model view**:

1. Create dimension-to-fact relationships on validated keys.
2. Use one-to-many cardinality, with the dimension on the `1` side.
3. Use single-direction filtering from dimension to fact by default.
4. Keep many-to-many relationships out of the core model unless a real business relationship requires them and the filter behavior is fully understood.
5. For follows, use distinct role-playing profile dimensions or carefully designed measures; do not make both directions active just to get a visual working.
6. Hide surrogate keys and technical columns from report view where they are not useful.
7. Set column formats, default summarization, sort-by columns, display folders, descriptions, and hierarchies.
8. Disable Auto date/time for a controlled model that uses `DimDate`, if compatible with the project requirements.

### Required model checks

- Each dimension key is unique and non-null.
- Every fact foreign key either matches a dimension row or is explicitly handled as unknown/not applicable.
- No accidental many-to-many joins or ambiguous active paths.
- Row counts at each fact's declared grain are unchanged after shaping.
- A visual's totals reconcile to a simple source query or QA summary.
- Every date relationship uses a date-only key, not a timestamp with a time component.

## 6. DAX measures: explicit, defined, and testable

Create a dedicated measures table (for example, enter a one-column table in **Home → Enter data**, name it `_Measures`, then hide its helper column). Create measures with **Modeling → New measure**. Align names with your actual model fields.

The following examples assume the indicated tables and columns exist. Adjust only after checking the real curated query schema.

```dax
Post Count =
DISTINCTCOUNT ( FactPosts[status_id] )

Like Events =
COUNTROWS ( FactLikes )

Comment Events =
COUNTROWS ( FactComments )

Media Items =
COUNTROWS ( FactMedia )

Profiles =
DISTINCTCOUNT ( DimProfile[id] )

Average Stored Likes per Post =
DIVIDE (
    SUM ( FactPosts[likes_count] ),
    [Post Count]
)

Likes per Post (Event Grain) =
DIVIDE (
    [Like Events],
    [Post Count]
)

Comments per Post =
DIVIDE (
    [Comment Events],
    [Post Count]
)

Posts per Active Profile =
DIVIDE (
    [Post Count],
    DISTINCTCOUNT ( FactPosts[profile_id] )
)
```

### Deleted rows and metric definitions

If soft-deleted likes/comments should be excluded, use a clearly named measure and confirm the exact deletion column type:

```dax
Visible Like Events =
CALCULATE (
    COUNTROWS ( FactLikes ),
    ISBLANK ( FactLikes[deleted_at] )
)
```

This assumes `deleted_at` exists and blank means not deleted. If the column is absent, named differently, or represented by a different sentinel, update the measure to match the actual contract. Do not silently mix all-source counts and visible-event counts.

### Time-intelligence examples

With `DimDate[Date]` marked as the date table and an active relationship to `FactPosts[created_date]`:

```dax
Posts YTD =
TOTALYTD ( [Post Count], DimDate[Date] )

Posts Previous Month =
CALCULATE (
    [Post Count],
    DATEADD ( DimDate[Date], -1, MONTH )
)

Posts MoM Change =
[Post Count] - [Posts Previous Month]

Posts MoM Change % =
DIVIDE ( [Posts MoM Change], [Posts Previous Month] )
```

Use a complete, contiguous date dimension and test behavior when the previous period has no rows. Decide whether a blank or zero is appropriate; do not replace every blank with zero automatically.

### Filter-role example for an inactive date relationship

If `FactPosts[updated_date]` has an inactive relationship to `DimDate[Date]`:

```dax
Posts Updated by Selected Date =
CALCULATE (
    [Post Count],
    USERELATIONSHIP ( FactPosts[updated_date], DimDate[Date] )
)
```

### DAX best practices

- Prefer measures to calculated columns for aggregations; use Power Query for stable row-level shaping where practical.
- Use `DIVIDE` for ratios to handle zero denominators.
- Reuse base measures instead of duplicating business logic.
- Avoid `SUMX(Fact, RELATED(...))` when a normal aggregation or correct relationship can do the job.
- Use `DISTINCTCOUNT` only when the business definition calls for unique entities; it is not a generic fix for duplicated joins.
- Use variables for repeated expressions and readability.
- Format percentage measures as Percentage in model formatting; do not multiply by 100 if using the Percentage format.
- Separate source-stored counters from event-table counts.
- Keep measures explicit and hide raw numeric columns that users should not aggregate directly.

## 7. Report UX and accessibility

Recommended initial pages:

1. **Overview** — post count, visible engagement events, active profiles, posting trend, content visibility/type mix.
2. **Content performance** — posts by date, format, visibility, and creator cohort; distinguish stored counters from event counts.
3. **Engagement** — likes/comments over time, engagement by creator/profile, with fact-grain-safe measures.
4. **Federation** — local versus remote profiles/content and activity by instance/domain, if those attributes exist in the curated model.
5. **Stories and media** — story views, media mix, and temporal patterns.
6. **Data quality** (developer-facing) — refresh timestamp, row counts, orphan/duplicate counts, and validation status.

Design rules:
- Use descriptive titles and subtitles that define the metric and period.
- Keep slicers consistent across pages and avoid unnecessary slicer proliferation.
- Use tooltips for definitions, not as the only place where critical context appears.
- Provide alt text for meaningful visuals, keyboard-friendly navigation, sufficient contrast, and do not rely on color alone.
- Use drill-through only where the destination provides a meaningful detail view.
- Keep sensitive user-level details out of public-facing pages and exported data.

## 8. Performance, refresh, and modern project workflow

- Use Power Query's Query Diagnostics when refresh behavior is unexpectedly slow.
- Filter rows and remove unused columns early when it does not break source semantics; avoid repeated expensive sorts and per-row table scans.
- Keep transformations simple and foldable when using fold-capable database sources. Local CSV/JSON/Excel files generally do not provide database query folding.
- Disable load for intermediate staging and QA queries when only their curated dependents need loading. Validate that referenced queries still refresh as expected.
- Use Performance Analyzer (View → Performance Analyzer) to identify slow visuals, then inspect DAX and model cardinality.
- Prefer Import mode for this local file-based portfolio unless a supported DirectQuery source and a clear latency/scale requirement justify another mode.
- Incremental refresh is most useful for supported sources and large partitionable fact tables with a stable date/time column and RangeStart/RangeEnd parameters. It is not a magic optimization for a small local CSV/JSON landing zone; verify connector support before designing around it.
- Use PBIP/TMDL versioning only where supported by the installed Power BI Desktop version. Review diffs carefully, keep local paths configurable, and test model opening/refresh after metadata changes.
- Keep development, test, and production source paths/configuration separate if the project grows beyond local development.
- Do not store credentials or secrets in M source code, report files, Git, or documentation.

## 9. Release checklist

Before committing or publishing a model:

- [ ] Landing validator passes against the existing `data/landing` directory.
- [ ] Query names/groups and descriptions are consistent.
- [ ] Data types, null handling, and timestamp semantics are documented.
- [ ] Duplicate primary keys and orphan foreign keys have been checked.
- [ ] Every fact grain and metric definition is documented.
- [ ] Dimension keys are unique; relationship cardinality and direction are correct.
- [ ] `DimDate` is marked as the date table and sort-by columns are set.
- [ ] Measures are explicit, formatted, and tested against known row counts.
- [ ] Report visuals are accessible and do not imply unsupported causal conclusions.
- [ ] Refresh succeeds on a clean session with the intended source path/ODBC setup.
- [ ] No credentials, private messages, or unnecessary PII are exposed.
- [ ] The PBIP/model changes and documentation are reviewed in a feature branch and merged through a Pull Request.

## 10. Official references

Power BI Desktop and DAX capabilities evolve. Check the current Microsoft documentation for version-specific UI labels and feature availability:

- [Power Query documentation](https://learn.microsoft.com/power-query/)
- [Power Query M formula language](https://learn.microsoft.com/powerquery-m/)
- [Power BI star schema guidance](https://learn.microsoft.com/power-bi/guidance/star-schema)
- [DAX overview](https://learn.microsoft.com/dax/dax-overview)
- [DAX function reference](https://learn.microsoft.com/dax/)
- [Power BI performance analyzer](https://learn.microsoft.com/power-bi/create-reports/desktop-performance-analyzer)
- [TMDL view](https://learn.microsoft.com/power-bi/transform-model/desktop-tmdl-view)
- [Incremental refresh](https://learn.microsoft.com/power-bi/connect-data/incremental-refresh-overview)
- [Power BI accessibility](https://learn.microsoft.com/power-bi/create-reports/desktop-accessibility-creating-reports)
