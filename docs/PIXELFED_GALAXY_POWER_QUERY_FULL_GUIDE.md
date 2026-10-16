# PixelFed Analytics Engineering — Complete Power Query Galaxy Build Guide

This guide assumes your 54 `stg_<table>` queries are already imported successfully. It focuses on the steps that come next: data-quality checks, null/error handling, dynamic `DimDate` and `DimTime`, curated dimensions, fact/bridge grain, and safe modeling. Perform standard transformations in the Power Query GUI; use Advanced Editor only for the timestamp inventory and dynamic date/time dimensions included below. No TMDL scripts are required.

**Landing directory:** `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`  
**Build sequence:** Chapter 1 → Chapter 2 → Chapter 3.

---
## Chapter 1 — Data Quality in Power Query (GUI-first)
This stage assumes all 54 `stg_<table>` staging queries have already been imported successfully. Do not import them again and do not repair source issues by silently editing the staging queries. Build separate `qa_` queries to identify problems, then make deliberate corrections in referenced curated queries.

**Project landing path:** `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`  
**Schema contract:** [`../../schema.md`](../../schema.md)  
**Next:** [03 — Dimensions](#chapter-2-build-the-dimension-layer-in-power-query) → [04 — Facts & Bridges](#chapter-3-build-facts-and-bridges-in-power-query)

---

## 1. Organize the query workspace

1. Open **Power BI Desktop → Home → Transform data**.
2. In the Queries pane, create these groups: `01 Staging`, `02 Data Quality`, `03 Dimensions`, `04 Facts & Bridges`, and `99 Scratch`.
3. Move the existing `stg_` queries into `01 Staging` without changing their source steps.
4. Keep all quality queries named `qa_<subject>_<check>`, for example `qa_likes_duplicate_id` or `qa_profiles_orphan_user`.
5. Add a query description (right-click a query → Properties, if available in your version) that states what it checks and what a returned row means.

Keep QA queries as diagnostic outputs. Disable load for QA queries after the issues are reviewed; while developing, temporarily load a small QA result if you need to inspect it in Data view.

## 2. Profile data before changing it

For each important table:

1. Select the query, then open **View**.
2. Enable **Column quality**, **Column distribution**, and **Column profile**.
3. In the profiling status bar, change profiling from **Top 1000 rows** to **Entire data set** before sign-off.
4. Inspect key columns first, then foreign keys, timestamps, flags, counts and optional descriptive text.
5. Record the source table, column, issue, affected row count, decision and validation performed in your project notes.

Start with `stg_users`, `stg_profiles`, `stg_statuses`, `stg_likes`, `stg_comments`, `stg_media`, `stg_followers`, `stg_bookmarks`, `stg_status_hashtags`, `stg_mentions`, `stg_stories`, `stg_story_views`, and the SQLite/ODBC tables.

Do not read the green/valid percentage as proof that a column is semantically correct. Profiling detects distributions, blanks and errors; it cannot determine whether a user ID was joined to the right entity.

## 3. Create primary-key checks using only the GUI

Repeat these steps for each primary key in the source schema:

1. Right-click the relevant `stg_` query and choose **Reference**.
2. Rename the new query, e.g. `qa_likes_duplicate_id`.
3. Keep only the key column (Home → Choose Columns). For a composite key check, keep all columns in the specified pair/triple.
4. Select **Home → Group By**. Use **Advanced** for a composite key. Group by the key column(s) and create an operation named `RowCount` with operation **Count Rows**.
5. Filter `RowCount` to values greater than 1. The resulting rows are duplicate key values.
6. Create a second QA query from the staging table, filter the key column to **is null**, and name it `qa_<table>_null_key`.
7. Inspect the source rows behind each finding before correcting anything.

For single primary keys such as `users.id`, `profiles.id`, `statuses.id`, `likes.id`, `comments.id`, `media.id`, `followers.id` and `story_views.id`, the expected result is zero duplicate groups and zero null primary keys.

For documented composite uniqueness, also test:

| Table | Group-by columns that should be unique together |
|---|---|
| `likes` | `profile_id`, `status_id` |
| `followers` | `profile_id`, `following_id` |
| `bookmarks` | `status_id`, `profile_id` |
| `status_hashtags` | `status_id`, `hashtag_id` |
| `circle_profiles` | `circle_id`, `profile_id` |
| `discover_category_hashtags` | `discover_category_id`, `hashtag_id` |
| `story_views` | `story_id`, `profile_id` |
| `direct_messages` | `to_id`, `from_id`, `status_id` |
| `hashtag_follows` | `user_id`, `profile_id`, `hashtag_id` |

Do not use **Remove Duplicates** as a substitute for understanding why a declared unique key is duplicated. Preserve a QA result and document the resolution.

## 4. Find orphan foreign keys using a Left Anti join

A foreign key can be null and valid if the schema marks it nullable. An orphan is a **non-null key with no matching parent row**.

Example: validate `likes.status_id` against `statuses.id`.

1. Right-click `stg_likes` → **Merge Queries as New**.
2. Select `stg_statuses` as the second table.
3. Select `status_id` in the first table, then `id` in the second table.
4. Choose **Left Anti (rows only in first)** as the join kind.
5. Name the result `qa_likes_orphan_status`.
6. Inspect the returned rows and check their status IDs. A non-empty result means the child key has no parent match.

For optional foreign keys, first create a referenced QA query and filter the foreign-key column to **is not null**, then run the Left Anti join. This avoids treating valid nulls as orphans. Use this process for:

| Child field | Parent key | Null policy |
|---|---|---|
| `profiles.user_id` | `users.id` | Null is valid for remote profiles; anti-join only non-null values. |
| `users.profile_id` | `profiles.id` | Nullable; check non-null values as an independent reverse-link test. |
| `statuses.profile_id` | `profiles.id` | Nullable per source schema; preserve nulls and test non-null values. |
| `statuses.place_id` | `places.id` | Nullable; preserve nulls. |
| `likes.status_id` | `statuses.id` | Required; any null/orphan is a quality failure. |
| `likes.profile_id` | `profiles.id` | Required; any null/orphan is a quality failure. |
| `comments.status_id` / `comments.profile_id` | `statuses.id` / `profiles.id` | Required; validate both. |
| `media.status_id` / `media.profile_id` / `media.user_id` | `statuses.id` / `profiles.id` / `users.id` | Nullable according to schema; only non-null values are anti-joined. |
| `followers.profile_id` / `followers.following_id` | `profiles.id` / `profiles.id` | Both endpoints must resolve to profiles; `following_id` is a profile ID, not `followers.id`. |
| `status_hashtags.status_id` / `hashtag_id` | `statuses.id` / `hashtags.id` | Required. `profile_id` is nullable. |
| `story_views.story_id` / `profile_id` | `stories.id` / `profiles.id` | Required. |
| `notifications.profile_id` / `actor_id` | `profiles.id` / `profiles.id` | Recipient required; actor nullable. |

**Schema interpretation warning:** `schema.md` lists a suspicious `followers.id → follow_requests.follower_id` relationship. The child field `follower_id` is semantically a profile identity, while `followers.id` is the ID of a follow-edge row. Validate `follow_requests.follower_id` and `following_id` against `profiles.id`; do not wire the suspicious relationship into the model without evidence from the actual source database.

## 5. Validate identity without confusing ID domains

The values in `users.id` and `profiles.id` can overlap and still refer to different entities. Never join those tables on `id = id`.

- Correct primary user/profile link: `profiles.user_id` → `users.id`.
- Reverse link check: `users.profile_id` → `profiles.id`.
- These links are not guaranteed to be one-to-one by every constraint in the schema. Use anti-joins and duplicate checks to measure actual behavior.
- Keep remote profiles whose `user_id` is null. Do not remove them simply because they have no local account row.
- For user-to-profile attributes, use a **Left Outer** merge from profiles to users on `profiles.user_id = users.id`; expand only explicitly needed and safe account attributes. Confirm the row count did not increase after expansion.

## 6. Null, blank and soft-delete policies

Use the following defaults, then adapt only when the business meaning is documented:

| Field scenario | Correct default | Avoid |
|---|---|---|
| Required key is null | Capture in QA; exclude from curated table only under a documented rule. | Fabricating a key or quietly removing the row. |
| Nullable foreign key is null | Preserve null; it can be a valid absent relationship. | Replacing it with 0 or `Unknown` in staging. |
| Optional timestamp is null | Keep null; it means no recorded timestamp. | Replacing it with refresh time or a fake date. |
| Optional numeric count is null | Preserve as unknown unless the source contract says null means zero. | Replacing every null with zero. |
| Text is empty or whitespace | Use Transform → Format → Trim/Clean. Replace empty text with null only if empty and missing mean the same thing. | Global replace across every text column. |
| Soft-delete column such as `deleted_at` | Keep the row and the deletion timestamp in staging. Apply an explicit active-record filter only in a specific curated query/measure. | Permanently deleting soft-deleted records in staging. |
| JSON/serialized field is null | Preserve raw null. Parse only the fields needed for a defined use case. | Expanding every JSON field in every table. |
| Binary-like ODBC key | Verify the underlying source and use an explicit SQL text cast before an intentional numeric conversion if it is truly a numeric field. | Converting arbitrary bytes to number. |

## 7. Correct conversion errors instead of hiding them

When a type-conversion step creates errors:

1. Click the error cell and read **Error** details.
2. Right-click the query and choose **Reference** to create an investigation query.
3. Use Home → Keep Rows → Keep Errors (or filter to the affected rows) to isolate failures.
4. Inspect the raw value, source column, culture/date format and ODBC metadata.
5. Fix the source projection or conversion step only after determining the reason.
6. Keep a QA row count before and after the correction.

Do not add **Remove Errors** as a generic last step. Microsoft documents that it removes entire rows containing errors, which can hide source-quality issues. See [Dealing with errors in Power Query](https://learn.microsoft.com/en-us/power-query/dealing-with-errors).

## 8. ODBC Binary ID handling

For the 13 SQLite tables, inspect the `Source` step before trusting a `Changed Type` step. The implemented workaround explicitly casts numeric ID fields to text in the SQLite SQL projection and then converts the resulting readable digits to Whole Number in Power Query. String IDs such as OAuth IDs and session IDs must remain text.

1. Open a failing `stg_` ODBC query → Advanced Editor.
2. Verify the SQL selects explicit columns rather than `SELECT *` and casts the affected integer key to text at the source.
3. Verify the next step converts the readable text to Whole Number (`Int64.Type`).
4. Preview the source step and the typed step. Confirm value preservation, null preservation and no conversion errors.
5. Do not apply numeric conversion to `sessions.id`, `oauth_access_tokens.id`, `oauth_auth_codes.id`, token text or other string keys.

For `jobs` and `sessions.last_activity`, integer fields may be Unix epoch values rather than ordinary numeric IDs. Check a few raw values and confirm seconds versus milliseconds before converting them into dates. Do not allow those integer columns into the dynamic timestamp inventory until their unit has been confirmed and converted.

## 9. Exit criteria before creating dimensions

- [ ] Primary-key null and duplicate checks have been run for every key used by a dimension or fact.
- [ ] Required foreign keys are checked for nulls and unmatched parents.
- [ ] Optional foreign keys are anti-joined only after filtering to non-null values.
- [ ] `profiles.user_id` and `users.profile_id` have been checked independently.
- [ ] Documented composite unique pairs have been tested.
- [ ] ODBC numeric IDs are readable and typed consistently; text IDs stay text.
- [ ] Errors are understood, not hidden by a blanket Remove Errors step.
- [ ] Null, blank, soft-delete and sensitive-column policies are documented.
- [ ] Staging row counts still reconcile to the landing metadata.

Only then continue to [03 — Dimensions](#chapter-2-build-the-dimension-layer-in-power-query).

## Microsoft references

- [Power Query best practices](https://learn.microsoft.com/en-us/power-query/best-practices)
- [Power Query data profiling](https://learn.microsoft.com/en-us/power-query/data-profiling-tools)
- [Dealing with errors](https://learn.microsoft.com/en-us/power-query/dealing-with-errors)
- [Power Query referenced queries](https://learn.microsoft.com/en-us/power-bi/guidance/power-query-referenced-queries)

---

## Chapter 2 — Build the Dimension Layer in Power Query
**Starting point:** your `stg_<table>` queries are already imported. Complete the QA checks in [02 — Data Quality](#chapter-1-data-quality-in-power-query-gui-first) first. This chapter focuses on the Power Query GUI, with M in Advanced Editor only for reusable, dynamic date/time dimensions.

## 1. Set up the dimension group

In **Transform data**:

1. Create a query group named `03 Dimensions`.
2. For every dimension, right-click its `stg_` source → **Reference**. Do not change the staging query and do not use Duplicate unless you intentionally need an independent copy of the source logic.
3. Rename the query to `Dim...`.
4. Use **Home → Choose Columns** to keep only the fields required for slicing and grouping.
5. Rename source IDs to semantic names, set explicit types, review nulls, and verify that the dimension key is unique before Close & Apply.
6. Add a query description: “One row per …” plus a one-sentence explanation.

Power Query references are logical dependencies, not guaranteed cached materializations. Keep dimension transformations lean and avoid repeating large merges unnecessarily. See [referenced-query guidance](https://learn.microsoft.com/en-us/power-bi/guidance/power-query-referenced-queries).

## 2. `DimUser` — one row per `users.id`

**GUI steps**

1. Right-click `stg_users` → Reference; name it `DimUser`.
2. Choose columns: `id`, `profile_id`, `name`, `username`, `status`, `language`, `is_admin`, `email_verified_at`, `created_at`, `deleted_at`. Add `email` only if there is a documented reporting use and the model is access-controlled.
3. Do **not** keep `password`, `remember_token`, `2fa_secret`, `2fa_backup_codes`, `2fa_setup_at`, or security credentials in the reporting dimension.
4. Rename `id` → `UserID`; `profile_id` → `PrimaryProfileID`; `created_at` → `AccountCreatedAt`; `deleted_at` → `AccountDeletedAt`; `email_verified_at` → `EmailVerifiedAt`.
5. Apply Whole Number to IDs and Date/Time to timestamps; keep status and language as Text. Treat `is_admin` as a validated 0/1 flag, not an arbitrary number.
6. Run the `DimUser[UserID]` unique/non-null checks from the QA chapter.

Do not equate a UserID with a ProfileID even if the numbers happen to match. Use the explicit relationship columns only.

## 3. `DimProfile` — one row per `profiles.id`

1. Reference `stg_profiles`; name the query `DimProfile`.
2. Keep `id`, `user_id`, `domain`, `username`, `status`, `name`, `location`, `website`, `profile_layout`, `post_layout`, `is_private`, `is_suggestable`, `status_count`, `followers_count`, `following_count`, `created_at`, `updated_at`, `deleted_at`.
3. Exclude `private_key`, `public_key`, federation key data, and unnecessary URL/payload fields from the report-facing dimension.
4. Rename `id` → `ProfileID` and `user_id` → `UserID`; rename timestamps and counts to readable names.
5. Preserve null `UserID` values because remote profiles may not have a local user row.
6. Validate `ProfileID` uniqueness. Check non-null `UserID` values against `DimUser[UserID]` using the QA anti-join process.

**Optional enrichment:** to bring an account attribute into a profile dimension, use Home → Merge Queries, joining `DimProfile[UserID]` to `DimUser[UserID]` with **Left Outer**. Expand only safe columns. Recheck row count and `ProfileID` uniqueness immediately after expanding. Don't merge in both directions or infer a join from same-looking integer IDs.

## 4. `DimStatus` — one row per `statuses.id`

1. Reference `stg_statuses`; name it `DimStatus`.
2. Keep `id`, `profile_id`, `place_id`, `type`, `visibility`, `scope`, `is_nsfw`, `reply`, `local`, `comments_disabled`, `language`, `likes_count`, `reblogs_count`, `reply_count`, `created_at`, `deleted_at`.
3. Rename `id` → `StatusID`, `profile_id` → `AuthorProfileID`, `place_id` → `PlaceID`, and the key descriptive fields consistently. Rename counters explicitly as `StoredLikesCount`, `StoredReblogsCount`, and `StoredReplyCount`.
4. Apply Whole Number to IDs/counters, Text to descriptive fields, and Date/Time to timestamps. Convert flags to True/False only after confirming non-null values are 0/1.
5. Keep null author/place IDs if the schema allows them; validate only non-null values against the relevant dimension.
6. Validate one row per `StatusID`.

**Important:** these counters describe the current stored status row. They are not historical snapshots and are not guaranteed to equal rows in `FactLikes` or `FactComments`. Keep the fields on `DimStatus` rather than creating a needless one-to-one `FactPostMetrics` table. Use explicitly named measures over the stored counters.

## 5. Other descriptive dimensions

Apply the same Reference → Choose Columns → Rename → Types → Key QA sequence.

| Dimension | Source | One row per | Recommended columns |
|---|---|---|---|
| `DimHashtag` | `stg_hashtags` | `hashtags.id` | ID, name, slug, NSFW/banned flags, created date |
| `DimPlace` | `stg_places` | `places.id` | ID, slug, name, country, latitude, longitude; coordinates are nullable decimal numbers and must be in valid geographic ranges |
| `DimStory` | `stg_stories` | `stories.id` | ID, profile/creator ID, type, MIME, public/local flags, expiry/created date and stored counters; leave raw JSON payload out |
| `DimCollection` | `stg_collections` | `collections.id` | ID, profile ID, title, visibility, NSFW flag, published/created dates; no long description unless required |
| `DimCircle` | `stg_circles` | `circles.id` | ID, owner profile, name, scope, active flag, created date; do not expose private message/address details |
| `DimDiscoverCategory` | `stg_discover_categories` | `discover_categories.id` | ID, name, slug, active flag, order, filter flags and active-until date |
| `DimInstance` | `stg_instances` | `instances.id` | ID, domain, name, banned/unlisted/auto-CW flags, created date; omit admin URLs and internal limit reasons unless required |
| `DimApp` (optional) | distinct `app_id` from `stg_websockets_statistics_entries` | one app ID | `AppID`; create only if useful app IDs actually exist |

For each dimension, use Group By on the key with Count Rows; any count above 1 needs investigation. Do not remove duplicate names from dimensions when the schema only guarantees unique IDs; usernames can repeat across domains and display names are not keys.

## 6. Role-playing profile dimensions

Several facts have more than one profile role. If you reuse one `DimProfile` for two roles, Power BI may create ambiguous active relationships. Create a separate role-playing query for each needed role:

1. Right-click `DimProfile` → **Reference**.
2. Rename the new query, e.g. `DimLikerProfile`.
3. Keep the same `ProfileID` key and only the descriptive columns needed in reports.
4. If column clarity helps, rename `ProfileID` for that role (e.g. `LikerProfileID`). The values must remain identical to `DimProfile[ProfileID]`.
5. Validate the role dimension has one row per key.

Create only those role dimensions used by loaded facts:

- `DimAuthorProfile` → `DimStatus[AuthorProfileID]`
- `DimLikerProfile` → `FactLikes[LikerProfileID]`
- `DimCommenterProfile` → `FactComments[CommenterProfileID]`
- `DimMediaOwnerProfile` → `FactMedia[MediaOwnerProfileID]`
- `DimFollowerProfile` and `DimFollowedProfile` → each endpoint in `FactFollows`
- `DimBookmarkingProfile` → `FactBookmarks[BookmarkingProfileID]`
- `DimMentionedProfile` → `FactMentions[MentionedProfileID]`
- `DimStoryViewerProfile` → `FactStoryViews[StoryViewerProfileID]`
- `DimNotificationRecipientProfile` and `DimNotificationActorProfile` → the corresponding notification profile roles

Do not connect all these copies back to base `DimProfile` as well as the facts; that creates unnecessary filter paths. Treat the role dimensions as the corresponding role endpoints in the model.

## 7. Create a dynamic timestamp inventory (one helper query)

This helper reads timestamps directly from the already imported staging queries. It does **not** use hard-coded min/max dates. It only includes timestamp columns selected for the event/date roles in this model. When you add another fact/date role later, add its source table and timestamp columns to the inventory.

1. In Power Query, choose **Home → New Source → Blank Query**.
2. Rename it `qEventTimestampValues`.
3. Open **Advanced Editor** and replace its contents with the M below.
4. Select Done, inspect the `Timestamp` column type and errors, then disable load for this helper. It is an internal query feeding `DimDate` and `DimTime`.

```powerquery
let
    SourceSpecs = {
        [TableName = "statuses", Data = stg_statuses, Columns = {"created_at", "deleted_at"}],
        [TableName = "likes", Data = stg_likes, Columns = {"created_at", "deleted_at"}],
        [TableName = "comments", Data = stg_comments, Columns = {"created_at", "rendered_at"}],
        [TableName = "media", Data = stg_media, Columns = {"created_at", "processed_at", "deleted_at"}],
        [TableName = "followers", Data = stg_followers, Columns = {"created_at"}],
        [TableName = "bookmarks", Data = stg_bookmarks, Columns = {"created_at"}],
        [TableName = "status_hashtags", Data = stg_status_hashtags, Columns = {"created_at"}],
        [TableName = "mentions", Data = stg_mentions, Columns = {"created_at", "deleted_at"}],
        [TableName = "stories", Data = stg_stories, Columns = {"created_at", "expires_at"}],
        [TableName = "story_views", Data = stg_story_views, Columns = {"created_at"}],
        [TableName = "notifications", Data = stg_notifications, Columns = {"created_at", "read_at", "deleted_at"}],
        [TableName = "account_logs", Data = stg_account_logs, Columns = {"created_at"}],
        [TableName = "activities", Data = stg_activities, Columns = {"created_at", "processed_at"}],
        [TableName = "websockets_statistics_entries", Data = stg_websockets_statistics_entries, Columns = {"created_at"}],
        [TableName = "reports", Data = stg_reports, Columns = {"created_at", "admin_seen"}],
        [TableName = "report_comments", Data = stg_report_comments, Columns = {"created_at"}],
        [TableName = "report_logs", Data = stg_report_logs, Columns = {"created_at"}],
        [TableName = "direct_messages", Data = stg_direct_messages, Columns = {"created_at", "read_at"}],
        [TableName = "contacts", Data = stg_contacts, Columns = {"created_at", "read_at", "responded_at"}],
        [TableName = "newsroom", Data = stg_newsroom, Columns = {"created_at", "published_at"}],
        [TableName = "import_datas", Data = stg_import_datas, Columns = {"created_at", "completed_at"}],
        [TableName = "import_jobs", Data = stg_import_jobs, Columns = {"created_at", "completed_at"}]
    },
    RecordsBySource =
        List.Transform(
            SourceSpecs,
            (spec as record) =>
                List.Combine(
                    List.Transform(
                        spec[Columns],
                        (columnName as text) =>
                            let
                                RawValues = try Table.Column(spec[Data], columnName) otherwise {},
                                TimestampRecords =
                                    List.Transform(
                                        RawValues,
                                        (rawValue as any) =>
                                            let
                                                Parsed = try DateTime.From(rawValue, "en-US") otherwise null
                                            in
                                                if Parsed = null then
                                                    null
                                                else
                                                    [SourceTable = spec[TableName], SourceColumn = columnName, Timestamp = Parsed]
                                    )
                            in
                                List.RemoveNulls(TimestampRecords)
                    )
                )
        ),
    AllRecords = List.Combine(RecordsBySource),
    Result =
        if List.IsEmpty(AllRecords) then
            #table({"SourceTable", "SourceColumn", "Timestamp"}, {})
        else
            Table.FromRecords(AllRecords),
    Typed = Table.TransformColumnTypes(
        Result,
        {{"SourceTable", type text}, {"SourceColumn", type text}, {"Timestamp", type datetime}},
        "en-US"
    )
in
    Typed
```

**Why explicit inventory instead of discovering every column ending in `_at`?** Some source fields such as `jobs.created_at`, `jobs.available_at`, `jobs.reserved_at` and `sessions.last_activity` are integers (often epoch values), not datetime values. Automatically treating every `_at` field as a timestamp could create false dates or enormous incorrect date ranges. Include an epoch column only after validating its unit and converting it correctly in its staging query.

## 8. `DimDate` — dynamic min/max from source data

1. **Home → New Source → Blank Query**; rename it `DimDate`.
2. Open **Advanced Editor** and use the query below. Its date boundaries are fetched from `qEventTimestampValues` every refresh, rounded to full calendar years, so you do not need to update the range manually.
3. Select Done and verify there are no date errors, no duplicate `Date` values, and no gaps in the calendar.
4. In Model view, mark `DimDate` as the date table using its `Date` column.
5. In Column tools, sort `MonthName` by `MonthNumber`, `MonthShortName` by `MonthNumber`, `DayName` by `DayOfWeekNumber`, and `YearMonth` by `YearMonthSort`.

```powerquery
let
    TimestampValues = List.RemoveNulls(qEventTimestampValues[Timestamp]),
    ObservedDates = List.Distinct(List.RemoveNulls(List.Transform(TimestampValues, each try Date.From(_) otherwise null))),
    HasObservedDates = not List.IsEmpty(ObservedDates),
    MinObservedDate = if HasObservedDates then List.Min(ObservedDates) else #date(2022, 1, 1),
    MaxObservedDate = if HasObservedDates then List.Max(ObservedDates) else Date.From(DateTime.LocalNow()),
    StartDate = Date.StartOfYear(MinObservedDate),
    EndDate = Date.EndOfYear(MaxObservedDate),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    AsTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    TypedDate = Table.TransformColumnTypes(AsTable, {{"Date", type date}}),
    AddDateKey = Table.AddColumn(TypedDate, "DateKey", each Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]), Int64.Type),
    AddYear = Table.AddColumn(AddDateKey, "Year", each Date.Year([Date]), Int64.Type),
    AddQuarterNumber = Table.AddColumn(AddYear, "QuarterNumber", each Date.QuarterOfYear([Date]), Int64.Type),
    AddQuarter = Table.AddColumn(AddQuarterNumber, "Quarter", each "Q" & Text.From([QuarterNumber]), type text),
    AddYearQuarter = Table.AddColumn(AddQuarter, "YearQuarter", each Text.From([Year]) & "-Q" & Text.From([QuarterNumber]), type text),
    AddMonthNumber = Table.AddColumn(AddYearQuarter, "MonthNumber", each Date.Month([Date]), Int64.Type),
    AddMonthName = Table.AddColumn(AddMonthNumber, "MonthName", each Date.MonthName([Date], "en-US"), type text),
    AddMonthShortName = Table.AddColumn(AddMonthName, "MonthShortName", each Text.Start(Date.MonthName([Date], "en-US"), 3), type text),
    AddMonthStart = Table.AddColumn(AddMonthShortName, "MonthStart", each Date.StartOfMonth([Date]), type date),
    AddYearMonth = Table.AddColumn(AddMonthStart, "YearMonth", each Text.From([Year]) & "-" & Text.PadStart(Text.From([MonthNumber]), 2, "0"), type text),
    AddYearMonthSort = Table.AddColumn(AddYearMonth, "YearMonthSort", each [Year] * 100 + [MonthNumber], Int64.Type),
    AddDayOfMonth = Table.AddColumn(AddYearMonthSort, "DayOfMonth", each Date.Day([Date]), Int64.Type),
    AddDayOfWeekNumber = Table.AddColumn(AddDayOfMonth, "DayOfWeekNumber", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    AddDayName = Table.AddColumn(AddDayOfWeekNumber, "DayName", each Date.DayOfWeekName([Date], "en-US"), type text),
    AddWeekStart = Table.AddColumn(AddDayName, "WeekStartMonday", each Date.StartOfWeek([Date], Day.Monday), type date),
    AddWeekNumber = Table.AddColumn(AddWeekStart, "WeekOfYearMondayStart", each Date.WeekOfYear([Date], Day.Monday), Int64.Type),
    AddDaysInMonth = Table.AddColumn(AddWeekNumber, "DaysInMonth", each Date.DaysInMonth([Date]), Int64.Type),
    AddIsWeekend = Table.AddColumn(AddDaysInMonth, "IsWeekend", each [DayOfWeekNumber] >= 6, type logical),
    Sorted = Table.Sort(AddIsWeekend, {{"Date", Order.Ascending}})
in
    Sorted
```

If `qEventTimestampValues` is empty, the fallback generates a development calendar from 2022 through the current year. Treat that as a warning: investigate why no timestamps were parsed rather than assuming the fallback is the real dataset range.

## 9. `DimTime` — dynamic distinct times observed in the data

This version derives distinct second-level times from the timestamps found in `qEventTimestampValues`. On refresh, newly observed times are added automatically. It is a **sparse, observed-time dimension**, not a full 86,400-row clock; every fact timestamp whose source was included in the inventory will have a corresponding observed time after refresh.

1. Create another **Blank Query** and name it `DimTime`.
2. Open Advanced Editor, paste the M below, select Done and set `TimeOfDay` to Time.
3. Confirm `TimeKey` is unique and `TimeOfDay` has no errors.
4. In the curated fact queries, create a time-only column from each event timestamp used for time-of-day analysis. Name it consistently (for example `CreatedTime`) and use the **Add Column → Time → Time Only** transform where available. Preserve the original timestamp.
5. Relate `DimTime[TimeOfDay]` to the fact's `CreatedTime` column only for the timestamp role intended to filter the fact. Use additional role-playing time dimensions if you need to filter by two time roles simultaneously.

```powerquery
let
    TimestampValues = List.RemoveNulls(qEventTimestampValues[Timestamp]),
    RawTimes = List.Transform(TimestampValues, each try Time.From(_) otherwise null),
    SecondPrecisionTimes =
        List.Transform(
            RawTimes,
            each if _ = null then null else #time(Time.Hour(_), Time.Minute(_), Number.RoundDown(Time.Second(_)))
        ),
    ObservedTimes = List.Sort(List.Distinct(List.RemoveNulls(SecondPrecisionTimes))),
    TimesToUse =
        if List.IsEmpty(ObservedTimes) then
            List.Times(#time(0, 0, 0), 86400, #duration(0, 0, 0, 1))
        else
            ObservedTimes,
    AsTable = Table.FromList(TimesToUse, Splitter.SplitByNothing(), {"TimeOfDay"}),
    TypedTime = Table.TransformColumnTypes(AsTable, {{"TimeOfDay", type time}}),
    AddTimeKey = Table.AddColumn(TypedTime, "TimeKey", each Time.Hour([TimeOfDay]) * 10000 + Time.Minute([TimeOfDay]) * 100 + Number.RoundDown(Time.Second([TimeOfDay])), Int64.Type),
    AddHour = Table.AddColumn(AddTimeKey, "Hour", each Time.Hour([TimeOfDay]), Int64.Type),
    AddMinute = Table.AddColumn(AddHour, "Minute", each Time.Minute([TimeOfDay]), Int64.Type),
    AddSecond = Table.AddColumn(AddMinute, "Second", each Number.RoundDown(Time.Second([TimeOfDay])), Int64.Type),
    AddMinuteOfDay = Table.AddColumn(AddSecond, "MinuteOfDay", each [Hour] * 60 + [Minute], Int64.Type),
    AddTimeLabel = Table.AddColumn(AddMinuteOfDay, "TimeLabel", each Time.ToText([TimeOfDay], [Format = "HH:mm:ss", Culture = "en-US"]), type text),
    AddAMPM = Table.AddColumn(AddTimeLabel, "AMPM", each if [Hour] < 12 then "AM" else "PM", type text),
    AddDayPart = Table.AddColumn(AddAMPM, "DayPart", each if [Hour] < 5 then "Overnight" else if [Hour] < 12 then "Morning" else if [Hour] < 17 then "Afternoon" else if [Hour] < 21 then "Evening" else "Late evening", type text),
    Sorted = Table.Sort(AddDayPart, {{"TimeOfDay", Order.Ascending}})
in
    Sorted
```

**Design note:** if you prefer every possible time even when not observed, use a complete one-second time dimension (86,400 rows) instead. The observed-time version above follows the requested data-driven approach. Avoid rounding fact timestamps to minutes unless you consciously want to lose seconds-level precision.

## 10. Create date/time role columns in facts

For each curated fact, preserve the original timestamp and add date/time-only columns. Example for `FactLikes`:

1. Right-click `stg_likes` → Reference; name it `FactLikes`.
2. Keep `id`, `profile_id`, `status_id`, `flagged`, `created_at`, `updated_at`, `deleted_at`.
3. Rename to `LikeID`, `LikerProfileID`, `StatusID`, `Flagged`, `CreatedAt`, `UpdatedAt`, `DeletedAt`.
4. Apply key/flag/timestamp types.
5. Select `CreatedAt` and use **Add Column → Date → Date Only**, rename the new column `CreatedDate`. Select `CreatedAt` again and use **Add Column → Time → Time Only**, rename the new column `CreatedTime`.
6. Preserve null `CreatedAt`; the generated `CreatedDate` and `CreatedTime` should also be null. Don't replace these with a sentinel date or midnight.

Repeat for `FactComments`, `FactMedia`, `FactFollows`, `FactBookmarks`, `BridgeStatusHashtag`, `FactMentions`, `FactStoryViews`, `FactNotifications` and any other event fact where date/time slicing is needed. Add matching source columns to `qEventTimestampValues` if necessary.

## 11. Validate before loading

- `DimDate[Date]` has no nulls, no duplicates and no gaps.
- `DateKey` is unique and stable for each date.
- `DimTime[TimeOfDay]` and `TimeKey` are unique.
- Every non-null fact `CreatedDate` exists in `DimDate[Date]`.
- Every non-null fact `CreatedTime` exists in `DimTime[TimeOfDay]`.
- Dimension keys are unique and typed exactly like the fact foreign keys.
- Disable load for `qEventTimestampValues` and base `DimProfile` if you use only its role-playing copies and do not need it separately in reports.
- Keep all source/security fields out of report-facing dimensions.

## Microsoft references

- [Power Query best practices](https://learn.microsoft.com/en-us/power-query/best-practices)
- [Power BI star schema](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [Date tables in Power BI](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-date-tables)

---

## Chapter 3 — Build Facts and Bridges in Power Query
This chapter starts after staging, data-quality QA and the core dimensions are ready. The rule is simple: **one fact/bridge row must mean one clearly stated thing**. Use Power Query to shape the source rows and Model view to create relationships. Do not flatten independent one-to-many events into one wide table.

Prerequisites: [02 — Data Quality](#chapter-1-data-quality-in-power-query-gui-first), [03 — Dimensions](#chapter-2-build-the-dimension-layer-in-power-query).

---

## 1. Repeatable build pattern (use for each fact)

1. In Power Query, right-click the corresponding `stg_` source → **Reference**.
2. Name the query `Fact...` or `Bridge...`.
3. Use **Home → Choose Columns** to keep the source primary key, foreign keys, date/time columns required for relationships, useful flags/measures and only necessary descriptors.
4. Rename IDs by their role (e.g. `profile_id` → `LikerProfileID` in `FactLikes`). Never rename unrelated ID domains to the same name if that hides their meaning.
5. Set explicit data types. IDs that are numeric should be Whole Number; UUID/token/session identifiers stay Text. Timestamps are Date/Time. Flags should be validated 0/1 before converting to True/False.
6. Add date-only and time-only columns from timestamps where useful; keep original timestamps and preserve nulls.
7. Run key checks: primary-key uniqueness, documented compound key uniqueness, required foreign keys, and non-null foreign-key anti-joins.
8. Compare row count before and after the transformations. A basic reference fact should usually keep the same number of rows. If it changes, know exactly which filtering/grouping step caused it.
9. Only merge a dimension for a specifically needed attribute or for QA. Expand the minimum columns, then recheck row count and key uniqueness.
10. Disable load on staging and QA only after curated tables refresh and QA is reviewed; load the curated facts and bridges.

## 2. Build the core engagement facts in this order

### 2.1 `FactLikes` — one row per `likes.id`

**Source:** `stg_likes`  
**Keep:** `id`, `profile_id`, `status_id`, `flagged`, `created_at`, `updated_at`, `deleted_at`.

1. Reference `stg_likes`; name the query `FactLikes`.
2. Keep only the listed fields.
3. Rename them `LikeID`, `LikerProfileID`, `StatusID`, `Flagged`, `CreatedAt`, `UpdatedAt`, `DeletedAt`.
4. Set the three IDs to Whole Number; `Flagged` to a validated logical flag if all non-null values are 0/1; timestamps to Date/Time.
5. Add `CreatedDate` using Add Column → Date → Date Only; add `CreatedTime` using Add Column → Time → Time Only. Preserve `CreatedAt`.
6. Verify `LikeID` is unique; verify the `(LikerProfileID, StatusID)` pair is unique as documented; validate both required relationships.
7. Preserve rows with non-null `DeletedAt` and flag the deleted state; decide in measures whether deleted likes count as active likes.

**Do not merge comments or media into `FactLikes`.** Those are independent one-to-many events.

### 2.2 `FactComments` — one row per `comments.id`

**Keep:** `id`, `profile_id`, `user_id`, `status_id`, `is_remote`, `created_at`, `rendered_at`, `updated_at`. Include comment text only for a defined use; avoid rendered/body fields in the default reporting model.

Rename `id` to `CommentID`, `profile_id` to `CommenterProfileID`, `user_id` to `UserID`, and `status_id` to `StatusID`. `UserID` may be null. Validate the profile/status references; validate user only when non-null. Create `CreatedDate` and `CreatedTime` from `created_at`. Keep the remote flag as validated 0/1 or logical.

### 2.3 `FactMedia` — one row per `media.id`

**Keep:** `id`, `status_id`, `profile_id`, `user_id`, `is_nsfw`, `remote_media`, `mime`, `size`, `orientation`, `filter_name`, `processed_at`, `created_at`, `deleted_at` (plus only approved additional fields).

Rename the identity roles explicitly: `MediaID`, `StatusID`, `MediaOwnerProfileID`, `UploaderUserID`. The three foreign-key fields are different roles; do not collapse them into one “UserID”. `StatusID`, owner profile and uploader may be nullable as documented. Do not remove media just because it has no linked status. Exclude SHA hashes, raw metadata, storage keys and remote/internal paths unless a specific, approved analytics requirement needs them. Create `CreatedDate`/`CreatedTime`, and optionally `ProcessedDate` if processing latency is a question. Check non-null keys against the matching parent dimension.

### 2.4 `FactFollows` — one row per directed `followers` record

**Keep:** `id`, `profile_id`, `following_id`, `local_profile`, `local_following`, `created_at`, `updated_at`.

Rename to `FollowID`, `FollowerProfileID`, `FollowedProfileID`, `LocalFollower`, `LocalFollowed`, `CreatedAt`, `UpdatedAt`. The `profile_id` and `following_id` values should both resolve to `profiles.id`; don't join `following_id` to `followers.id`. Validate unique `(FollowerProfileID, FollowedProfileID)`, both endpoint keys, and whether any self-follows exist. Preserve self-follow rows in the QA output rather than silently deleting them. Add `CreatedDate`/`CreatedTime`.

Keep `follow_requests` separate: a request is not the same business event as a completed follow.

### 2.5 `FactBookmarks` — one row per bookmark

Keep `id`, `status_id`, `profile_id`, `created_at`, `updated_at`. Rename to `BookmarkID`, `StatusID`, `BookmarkingProfileID`, etc. Validate the source primary key and unique `(StatusID, BookmarkingProfileID)` pair. Add date/time-only columns from `created_at`. Validate status and profile references.

### 2.6 `BridgeStatusHashtag` — one row per status/hashtag association

Keep `id`, `status_id`, `hashtag_id`, nullable `profile_id`, `status_visibility`, `created_at`, `updated_at`. Rename IDs to `StatusHashtagID`, `StatusID`, `HashtagID`, `ProfileID`.

Validate the `(StatusID, HashtagID)` pair and both required parent keys; preserve nullable `ProfileID`. Never deduplicate on `StatusID` alone: one status can have several hashtags. When measuring content by hashtag, count distinct statuses rather than bridge rows. With single-direction relationships, filtering a bridge by hashtag will not automatically filter back through `DimStatus` into every fact; handle hashtag analysis deliberately in the semantic model instead of enabling Both everywhere.

### 2.7 `FactMentions` — one row per mention

Keep `id`, `status_id`, `profile_id`, `local`, `created_at`, `updated_at`, `deleted_at`. Rename the profile role to `MentionedProfileID`. Validate status/profile parents and add date/time columns. Preserve soft-deleted rows and make the reporting inclusion rule explicit.

### 2.8 `FactStoryViews` — one row per story-view event

Keep `id`, `story_id`, `profile_id`, `created_at`, `updated_at`. Rename to `StoryViewID`, `StoryID`, `StoryViewerProfileID`. Validate unique `(StoryID, StoryViewerProfileID)` and the required parent keys. Add date/time columns from `created_at`. The event rows are not interchangeable with `stories.view_count`.

### 2.9 `FactNotifications` — one row per notification

Keep `id`, `profile_id`, `actor_id`, `item_id`, `item_type`, `action`, `created_at`, `read_at`, `deleted_at`. Rename `profile_id` to `NotificationRecipientProfileID` and `actor_id` to `NotificationActorProfileID`.

- Recipient is required; actor and item ID may be null.
- Preserve `item_type` alongside `item_id`: this is a polymorphic reference and cannot safely point to one generic dimension.
- Add `CreatedDate`/`CreatedTime`. Keep `ReadAt` and `DeletedAt` for separate analysis; if read date is needed as a date role, create a dedicated date role dimension or use a controlled inactive relationship later.
- Exclude message/rendered fields by default unless explicitly needed.

### 2.10 `FactAccountLogs` — one row per account log

Keep `id`, `user_id`, `item_id`, `item_type`, `action`, `created_at`, `updated_at`. Rename to `AccountLogID`, `UserID`, `ItemID`, `ItemType`, `Action`, `CreatedAt`, `UpdatedAt`. Validate the required user key. Keep the `item_id`/`item_type` pair together. Exclude IP address, user-agent strings, raw messages and JSON metadata from the public/reporting model by default. Add `CreatedDate`/`CreatedTime`.

### 2.11 `FactWebSocketUsage` — one row per statistics record

Source `stg_websockets_statistics_entries`. Keep `id`, `app_id`, `peak_connection_count`, `websocket_message_count`, `api_message_count`, `created_at`, `updated_at`. Rename to readable measure names, type counts as Whole Number and `app_id` as Text. Add date/time fields. Create `DimApp` from distinct non-null `app_id` only if it has useful diversity; validate uniqueness before relating.

---

## 3. Add the next bridge/fact wave after the core refresh is clean

| Curated table | Source | Grain | Data-cleaning focus |
|---|---|---|---|
| `BridgeDiscoverCategoryHashtag` | `stg_discover_category_hashtags` | One discover-category/hashtag pair | Test `(discover_category_id, hashtag_id)` uniqueness and both parent keys. |
| `BridgeCircleProfile` | `stg_circle_profiles` | One circle/profile membership | Test `(circle_id, profile_id)` uniqueness. Owner ID is nullable; validate it only when populated. |
| `FactHashtagFollows` | `stg_hashtag_follows` | One user/profile/hashtag follow record | Test unique `(user_id, profile_id, hashtag_id)` and all parent keys. This is an event/association, not a status hashtag. |
| `BridgeCollectionItem` | `stg_collection_items` | One item association within a collection | Keep `object_type` with `object_id`. Polymorphic `object_id` must not be joined to statuses unless the type has been explicitly filtered and validated. `order` may be nullable. |
| `FactFollowRequests` | `stg_follow_requests` | One follow request | Keep requested-from and requested-to profile roles, rejected/local flags and dates. Validate both endpoint IDs against profiles, not against `followers.id`. |
| `FactDirectMessages` | `stg_direct_messages` | One message record | Keep sender and recipient roles, status ID and timestamps only. Exclude from broad reporting unless there is an approved privacy-safe use. Validate `to_id`/`from_id` key domain against profiles before relationship creation. |
| `FactContacts` | `stg_contacts` | One contact/request record | Avoid message/response text in report facts; keep response-requested flag and read/responded/created timestamps when needed. Validate `user_id`. |
| `FactReports` | `stg_reports` | One report | Keep report ID, reporter user/profile roles, object type/id pair, reported profile ID, category flags and timestamps. `object_id` is polymorphic; don't join directly to statuses without type filtering. Exclude message/meta payloads. |
| `FactReportComments` | `stg_report_comments` | One report comment | Keep report ID, profile/user IDs and timestamps; exclude free-text comment unless specifically required and access controlled. Validate report/profile/user parents. |
| `FactReportLogs` | `stg_report_logs` | One moderation/report log | Keep log ID, profile, item type/id pair, action, system flag, dates; leave metadata JSON out of default reporting. |
| `FactActivities` | `stg_activities` | One activity record | Keep ID, actor/to profile roles, object type and created/processed dates. Parse `data` JSON only if the exact required properties have been identified. |

Build one at a time. Complete the QA tests for each before continuing to the next.

## 4. Operational and sensitive domains — keep out of the first galaxy

These tables may support a separate Operations/Admin model, but do not force all 54 source tables into the content analytics galaxy.

| Source tables | Suggested handling |
|---|---|
| `import_jobs`, `import_datas` | Optional operational facts: one row per job/import item; remove raw `media_json` and storage paths unless needed. Validate `job_id` where present. |
| `jobs`, `failed_jobs` | Optional queue health model. Keep safe status/count/timestamp fields only. `jobs.created_at`, `available_at`, `reserved_at` are integer fields; validate epoch seconds/milliseconds before converting. Exclude payload/exception text from general reporting. |
| `mod_logs` | Optional moderation activity fact; remove free-text messages and metadata unless a controlled use exists. |
| `user_devices`, `user_settings` | Do not load IPs, fingerprints, user agents, settings that reveal sensitive behavior, or unnecessary user-level detail into the general report model. Use only approved aggregated features. |
| `sessions`, `email_verifications`, `oauth_access_tokens`, `oauth_auth_codes`, `oauth_clients`, `oauth_personal_access_clients`, `oauth_refresh_tokens`, `password_resets`, `user_invites` | Keep out of the reporting model. These can expose session data, tokens, email verification/reset information, client secrets, keys or invite tokens. If used for an operational audit, project only explicitly approved non-secret fields. |
| `avatars`, `profile_sponsors` | Optional profile attributes only if required; omit remote paths, keys and JSON payloads unless needed. |
| `pages`, `newsroom`, `discover_categories`, `instances`, `migrations`, `circles`, `collections` | Descriptive/administrative entities. Create dimensions only if report questions require them; do not add them just because they exist. |

The staging layer can preserve the original schema for traceability, but curated tables are a privacy and usability boundary. Do not expose passwords, tokens, private keys, session payloads, device fingerprints, IP addresses or unnecessary message text in the semantic model.

## 5. Safe merge rules

Only merge if the attribute is needed or the operation is a QA test.

- A many-to-one lookup from a fact to a unique dimension can be reasonable, but the better default is usually to retain the foreign key and use a model relationship.
- Before expanding a merged table, check that the lookup side key is unique. A non-unique lookup expands one fact row into multiple rows.
- After expansion, compare row count before and after. Fact row count should not grow merely because a descriptive attribute was added.
- Never merge `FactLikes`, `FactComments` and `FactMedia` to form a single table. One status with 5 likes, 3 comments and 2 media items could become 30 rows.
- For polymorphic columns such as `(item_type, item_id)`, `(object_type, object_id)` and `(filterable_type, filterable_id)`, keep both columns together. Resolve the reference only after restricting `*_type` to a single verified entity type.

## 6. Add date/time columns without destroying timestamps

For each event fact:

1. Keep the timestamp column, e.g. `CreatedAt`.
2. Select it and use **Add Column → Date → Date Only**; rename the new column `CreatedDate`.
3. Select the original timestamp and use **Add Column → Time → Time Only**; rename the new column `CreatedTime`.
4. Set `CreatedDate` to Date and `CreatedTime` to Time.
5. Keep nulls; a null timestamp should create null date/time parts.
6. Only create these columns for timestamp roles that the model will actually analyze. Follow [03 — Dimensions](#chapter-2-build-the-dimension-layer-in-power-query) for the dynamic `DimDate` and `DimTime` definitions.

## 7. Relationships after curated queries pass QA

Create relationships in **Model view**, not by flattening query tables.

- Dimensions on the one side, facts/bridges on the many side.
- Use single-direction filter flow from dimensions to facts/bridges as the starting point.
- `DimStatus[StatusID]` → likes, comments, media, bookmarks, mentions and status-hashtag bridge.
- `DimHashtag[HashtagID]` → `BridgeStatusHashtag[HashtagID]`.
- Profile role dimensions connect to the corresponding profile-role columns, not all to the same generic profile key.
- `DimDate[Date]` and `DimTime[TimeOfDay]` connect to matching event date/time columns where appropriate.
- Use a separate `DimPostDate` (Reference of `DimDate`) for `DimStatus[CreatedDate]` if content creation date and event date must be filtered simultaneously.
- Do not create a relationship on a polymorphic ID without type-specific resolution.

For hashtag analysis, note that single-direction filters from hashtag to bridge do not automatically flow back to status/fact tables. Do not solve this by making every relationship bidirectional; handle hashtag-aware measure behavior deliberately in the semantic-model phase.

## 8. Final exit checklist

- [ ] Every fact/bridge has a written grain (one row per what?).
- [ ] Primary keys are unique and required keys are non-null.
- [ ] Composite uniqueness rules have been checked.
- [ ] Required and non-null foreign keys have zero unexplained orphans.
- [ ] Valid optional null foreign keys are preserved.
- [ ] Row counts match staging unless an intentional filter/grouping is documented.
- [ ] No one-to-many join has silently multiplied rows.
- [ ] Event counts are separate from stored counters.
- [ ] `CreatedAt` is preserved alongside `CreatedDate`/`CreatedTime` where needed.
- [ ] Security/personal fields are excluded from report-facing facts.
- [ ] Model relationships are one-to-many where expected and single-direction by default.

## Microsoft references

- [Power BI star schema](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [Power Query best practices](https://learn.microsoft.com/en-us/power-query/best-practices)
- [Manage relationships in Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/desktop-create-and-manage-relationships)
- [Power Query errors](https://learn.microsoft.com/en-us/power-query/dealing-with-errors)
