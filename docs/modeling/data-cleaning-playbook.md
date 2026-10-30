# PixelFed Analytics Engineering: Power Query Cleaning, Null Handling, and Galaxy Modeling Playbook

> **Scope:** This guide covers only the Power Query preparation and semantic data-modeling stage. It is a manual learning path, not a prebuilt implementation. Follow it in Power BI Desktop and write or edit M only when a transformation is awkward or repetitive in the UI. No TMDL script is required.

## Project settings

- Project: `pixelfed-analytics-engineering`
- Landing path: `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`
- Source contract: `schema.md` (54 source tables)
- Power BI work: Power Query Editor, then Model view
- Naming convention: source queries `stg_<table>`; quality queries `qa_<table>_<check>`; curated queries `Dim...`, `Fact...`, or `Bridge...`

The supplied data is generated synthetic data, not real PixelFed production records. The goal is realistic referential consistency and an accurate dimensional design, not to reconstruct real user IDs.

---

## 1. Know the layers before transforming anything

Use three logical layers in Power Query:

| Layer | Query names | Purpose | Load to semantic model? |
|---|---|---|---|
| Source/staging | `stg_users`, `stg_profiles`, etc. | Faithful copy of source fields, corrected source types, no business interpretation | Usually disable load after validation |
| Quality/audit | `qa_users_missing_key`, `qa_likes_orphan_status`, etc. | Finds problems without silently deleting evidence | Usually disable load; temporarily load during development if helpful |
| Curated model | `DimProfile`, `FactLikes`, etc. | Reporting-ready columns, defined grain, intentional null policy | Yes |

### In Power Query Editor

1. Open **Home → Transform data**.
2. In the Queries pane, create groups named `00 Parameters`, `01 Staging`, `02 Data Quality`, `03 Dimensions`, `04 Facts and Bridges`, and `99 Deprecated / Scratch`.
3. Move each existing `stg_` query into `01 Staging`.
4. Do not clean the original staging query beyond source-readability/type fixes. Preserve its lineage and original key columns.
5. Create curated queries using **right-click source query → Reference**. Prefer Reference over Duplicate when you want to reuse the upstream steps, but be aware that referenced queries may cause the source to be evaluated more than once during refresh.
6. Disable load for staging and QA queries only after the curated model has successfully loaded and the QA results have been reviewed.

## 2. Profile first; don't guess at the data

Before replacing nulls or deleting rows, profile representative tables and then the full dataset.

1. Select a staging query.
2. On **View**, enable **Column quality**, **Column distribution**, and **Column profile**.
3. Change the profile setting from **Top 1000 rows** to **Entire data set**.
4. Record row count, distinct count, unique count, empty values, errors, minimum/maximum for numeric fields, and minimum/maximum dates.
5. Repeat this first for `users`, `profiles`, `statuses`, `likes`, `comments`, `media`, `followers`, `status_hashtags`, `stories`, and the ODBC tables affected by Binary IDs.
6. Keep a separate short data-quality log in the project documentation: query, column, issue, treatment, reason, rows affected, and test used to verify the fix.

**Best practice:** during development, use a small subset only where it is safe and reversible. Before sign-off, set profiling to the entire dataset and refresh all queries. Column profiling can be based on the first 1,000 rows by default, so do not treat the initial preview as proof of whole-dataset quality.

## 3. Use the correct transformation order

For each staging query, follow this general order. The exact order can change if a source needs special handling, but keep it deliberate and documented.

1. **Source / Navigation** — connect to the one assigned format for that table.
2. **Select columns early** — remove fields that are not needed downstream, especially payloads, large rendered content, private keys, tokens, and other sensitive fields from report-facing queries.
3. **Filter rows early only when justified** — for example, exclude a clearly invalid source row from a curated query after first capturing it in a QA query. Don't discard soft-deleted rows from staging.
4. **Correct source types** — fix ODBC IDs that arrive as Binary before converting them to whole numbers. Remove incorrect automatically-generated `Changed Type` steps if they cause errors, then apply a controlled type step.
5. **Normalize text** — trim whitespace and convert empty strings to null only when blank and missing have the same business meaning.
6. **Apply explicit types** — `Int64.Type` for integer keys/counters, `type text` for identifiers/codes, `type date` for date-only values, and `type datetime` for timestamps.
7. **Add derived columns** — for example, event date derived from a timestamp, a deletion flag, or a validated 0/1 interpretation.
8. **Join only when needed** — merge to look up a descriptive attribute or audit a relationship; expand only the fields needed.
9. **Deduplicate, group, sort, or perform expensive steps late** unless they are needed to make a subsequent operation correct.
10. **Validate the result** — row counts, key uniqueness, null profile, errors, and unmatched foreign keys.

CSV, JSON and Excel files do not support database query folding. For SQLite/ODBC, folding depends on the driver, connector, native SQL query, and subsequent steps; never assume it continues after an `Odbc.Query` native SQL step. Keep source projection/casting in SQLite SQL where necessary, then avoid needless transformations downstream.

## 4. Null handling rules for this schema

A null is not automatically a bad record. Treat nulls according to the semantics of each field, not by replacing every null with zero, empty text, or the word `Unknown`.

| Field kind | Example in PixelFed | Recommended treatment | Do not do this |
|---|---|---|---|
| Required primary key | `users.id`, `profiles.id`, `statuses.id`, `likes.id` | Must be non-null and unique. Send failures to a QA query; exclude from curated model only after measuring and documenting them. | Do not invent an ID or silently remove the row without auditing. |
| Nullable foreign key | `profiles.user_id`, `statuses.profile_id`, `media.status_id`, `statuses.place_id`, `notifications.actor_id` | Preserve null. It may be valid, e.g. remote profile/no attached status/unknown actor. Test non-null values for unmatched IDs. | Do not replace null with `0` or join on display name. |
| Non-null foreign key with missing target | `likes.status_id`, `comments.status_id`, `story_views.story_id` | This is a referential-integrity failure. Capture the row in a left-anti join QA query and investigate. | Do not silently drop it or turn the key null without documenting why. |
| Optional timestamp | `deleted_at`, `read_at`, `email_verified_at`, `last_fetched_at` | Preserve null to mean no recorded event/state. Derive a separate boolean when useful, e.g. `IsDeleted = DeletedAt <> null`. | Do not replace with current date, midnight, or a fabricated date. |
| Nullable numeric metric | `profiles.followers_count`, `stories.view_count`, `media.size` | Preserve null when unknown/not recorded. Only use zero if the source/business definition establishes that null means zero. | Do not blanket-replace all null numeric values with 0. |
| Boolean-like `tinyint` | `is_private`, `is_nsfw`, `revoked`, `active` | Validate allowed values (normally 0/1); keep type consistently numeric or convert to logical with explicit mapping. | Do not assume every tinyint is a boolean; some tinyints are counters/enums. |
| Optional text | `profiles.location`, `statuses.caption`, `notifications.message` | Trim leading/trailing spaces; convert a blank string to null only where it has the same meaning as missing. | Don't replace every missing description with `N/A` in the source layer. |
| JSON / serialized content | `metadata`, `entities`, `data`, `media_json` | Preserve raw JSON in staging. Parse/expand only required properties in a downstream query; handle null and malformed payloads separately. | Don't expand all JSON fields blindly or make one row explode into many unintentionally. |
| Security/PII | `password`, tokens, private keys, session payload, IP address, device fingerprint | Do not select into report-facing curated tables. Keep only in restricted staging if a legitimate need exists. | Never expose them in a Power BI model or public repository. |
| Polymorphic references | `item_id` + `item_type`, `object_id` + `object_type`, `filterable_id` + `filterable_type` | Keep the ID and type pair together as a discriminator. Resolve to a dimension only after filtering to one known type. | Do not join `item_id` to `statuses.id` for all records regardless of type. |

### Null policy by major table

- **`users`**: `id` is mandatory; `username`, `status`, `language`, timestamps can be nullable as documented. Exclude `password`, remember token and 2FA fields from curated data.
- **`profiles`**: `id` is mandatory; `user_id` can be null for a remote profile. Do not remove those rows simply because there is no local user. Avoid selecting `private_key` or other federation key material.
- **`statuses`**: `profile_id`, dates, caption, `place_id`, and other optional fields can be null. Preserve them. `deleted_at` means soft delete; it is not a reason to delete the source record by default.
- **`likes` / `comments` / `media`**: dates can be null; `media.status_id` and some media keys are nullable. Keep media without a `status_id`; flag for QA rather than dropping it.
- **`followers`**: relationship rows require valid follower and followed profile identifiers; enforce the compound uniqueness specified by `profile_id, following_id`.
- **`status_hashtags`**: validate `status_id + hashtag_id` uniqueness and target-key matches; `profile_id` is nullable.
- **`stories` / `story_views`**: optional counts/dates must stay null if unknown; validate story and profile references.
- **`notifications`**: `actor_id`, `item_id`, `item_type`, action and dates may be null; do not force every notification to have a known actor or treat every item ID as a status ID.
- **ODBC SQLite tables**: cast numeric IDs in the source projection to a readable type before applying whole-number types. OAuth IDs, session IDs, email addresses and tokens are text identifiers and must remain text.

## 5. Handle conversion errors without hiding bad data

Do not add `try … otherwise null` to every column as a generic cure. It can turn invalid values into nulls and make the query appear clean when it is not.

For a numeric key that unexpectedly arrives as Binary:

1. Open the affected `stg_` query and inspect the **Source** step, not only the final table.
2. For a SQLite ODBC source, use a targeted native SQL projection that casts that column to text in SQLite; then convert the returned text to `Int64.Type` in Power Query. Use this only for columns that are truly integer keys/counters.
3. Keep string keys (`oauth_access_tokens.id`, `oauth_auth_codes.id`, `oauth_refresh_tokens.id`, `sessions.id`, and `password_resets.token`) as text.
4. Preview the converted values and compare several values to SQLite's raw values.
5. Check distinct counts and null counts before and after conversion. They should not change except where the source has a documented null.

For ordinary text-to-number/date conversion errors:

1. Duplicate/reference the query to create a `qa_..._conversion_errors` query.
2. Apply the same attempted type conversion in the QA query and retain rows that error.
3. Inspect the source value and error reason.
4. Correct known formatting problems or preserve the invalid value in a separate raw column while flagging the row.
5. Only replace an error with null when the business definition explicitly says an invalid value should be treated as unknown—and record the count.

Use **Home → Keep Rows → Keep Errors** during diagnosis, or create a dedicated error query; don't use **Remove Errors** as the first reaction. Microsoft's Power Query error guide distinguishes query-step errors from cell-level conversion errors: https://learn.microsoft.com/en-us/power-query/dealing-with-errors.

## 6. Create curated dimensions from staging queries

Create each curated query with **right-click a staging query → Reference**. Keep the raw staging table unchanged. In each dimension, select only the columns that are useful for slicing, grouping, and describing the entity. Use one row per entity and one unique key.

### 6.1 `DimDate` and date roles

**Grain:** one row per calendar date. It is a conformed dimension used by event facts.

Manual steps:

1. Build one date list using the non-null dates from the important event tables, such as `statuses.created_at`, `likes.created_at`, `comments.created_at`, `media.created_at`, `followers.created_at`, `bookmarks.created_at`, `mentions.created_at`, `story_views.created_at`, and `notifications.created_at`.
2. Ignore null date values while finding the minimum and maximum; don't make a fake date for null events.
3. Generate a continuous calendar from the minimum to maximum date. If the whole source set has no valid dates, use an explicitly documented development range instead of letting Min/Max fail.
4. Add Date, DateKey (`YYYYMMDD`), Year, Quarter, MonthNumber, MonthName, YearMonth, MonthStart, DayOfWeekNumber, DayOfWeek, and IsWeekend.
5. Apply explicit types. Sort MonthName by MonthNumber and DayOfWeek by DayOfWeekNumber.
6. In Model view, mark the query as the date table using its unique `Date` field.

Avoid multiple active routes between one date dimension, a status dimension, and event facts. A clear first design is `DimEventDate` linked directly to event timestamps and a referenced `DimPostDate` linked to `DimStatus[CreatedDate]`. Create additional role-playing date tables only when an analysis needs both event date and post creation date simultaneously.

### 6.2 `DimUser`

**Source:** `stg_users`. **Grain:** one row per `users.id`.

Keep `UserID`, username, status, language, account creation date, deletion date, and email verification date if needed. Do not select password, remember token, 2FA secret/backup codes, or other security columns. Validate that `UserID` is unique and non-null. Treat `deleted_at` as a state/date attribute; don't remove the user automatically.

Use `DimUser` for account-level facts such as `FactAccountLogs` and a media-uploader role if required. Do not join `users.id` to `profiles.id` merely because the numbers coincide.

### 6.3 `DimProfile`

**Source:** `stg_profiles`. **Grain:** one row per `profiles.id`.

Keep `ProfileID`, `UserID`, domain, username, status, selected profile layout, privacy/suggestability flags, location if report-safe, created/deleted dates, and optional stored profile counters for reconciliation only.

- `ProfileID` comes from `profiles.id`.
- `UserID` comes from `profiles.user_id`, and can be null for a remote profile.
- If you need safe account attributes, merge `stg_users` on `profiles.user_id = users.id` using a **Left Outer** join; expand only selected columns such as account status/language. Keep the profile even when no local user matches.
- Treat `users.profile_id` as an independent source relationship to validate, not as permission to equate the two ID domains.
- Avoid making `DimUser` and `DimProfile` active one-to-one relationship tables unless you have a tested requirement. Consolidating safe descriptive attributes in `DimProfile` is often simpler; keep `DimUser` as the account dimension for account-specific facts.

### 6.4 `DimStatus`

**Source:** `stg_statuses`. **Grain:** one row per `statuses.id`.

Keep `StatusID`, `AuthorProfileID` (source `profile_id`), post type, visibility, scope, NSFW flag, reply flag, language, local flag, comments-disabled flag, post creation date, deletion date, and optional `PlaceID`. Keep long captions/rendered content out unless a particular report requires them.

The source `statuses` table stores one current row per status and current counters such as `likes_count`, `reblogs_count`, and `reply_count`; it does **not** provide a historical counter snapshot grain. For the initial model, keep these as clearly named stored-counter attributes/measures on `DimStatus`, and don't create a separate `FactPostMetrics` table related 1:1 to `DimStatus`. Power BI one-to-one relationships filter in both directions and can cause ambiguity; Microsoft recommends avoiding them where the tables can be consolidated. If you later generate genuine history, create `FactPostSnapshots` at **one status per snapshot date** with a `SnapshotDate` and then relate it 1:* to dimensions.

Preserve null `profile_id` and `place_id` values. Don't convert them to zero. Validate that every non-null `AuthorProfileID` and `PlaceID` matches its dimension.

### 6.5 `DimHashtag`

**Source:** `stg_hashtags`. **Grain:** one row per hashtag.

Keep `HashtagID`, name, slug, NSFW flag, banned flag, and created date if useful. Validate unique `id`, `name`, and `slug` as documented. Normalize surrounding whitespace but don't arbitrarily rewrite a name/slug that represents a source key.

### 6.6 `DimPlace`

**Source:** `stg_places`. **Grain:** one row per place.

Keep `PlaceID`, slug, name, country, latitude, longitude. Convert latitude/longitude to decimal numbers. Flag values outside latitude `-90..90` or longitude `-180..180`; keep nullable coordinates null. Don't substitute a guessed location for missing coordinates.

### 6.7 `DimStory`

**Source:** `stg_stories`. **Grain:** one row per story.

Keep `StoryID`, creator `ProfileID`, type, public/local flags, expiry and creation timestamps, and optional stored view/comment counters. The event-based view count should come from `story_views`, not be confused with the story's stored counter. Keep expired stories in the data; use `expires_at` or an explicit `IsExpired` flag for reporting rather than deleting them during cleaning.

### 6.8 Role-playing profile dimensions

When a fact contains two different profile roles, create separate role-playing dimensions by using **Reference** on `DimProfile`, naming each copy for its role and retaining the same unique `ProfileID` key. Examples:

- `DimLikerProfile`
- `DimCommenterProfile`
- `DimFollowerProfile`
- `DimFollowedProfile`
- `DimBookmarkerProfile`
- `DimMentionedProfile`
- `DimStoryViewerProfile`
- `DimStoryCreatorProfile`
- `DimNotificationActorProfile`
- `DimNotificationRecipientProfile`

You don't need to create every copy immediately. Add only the roles needed by loaded facts. This is better than relating the same dimension to multiple columns and then dealing with inactive/ambiguous relationships in every report.

## 7. Build facts and bridge tables at declared grain

Use **Reference** from staging. Select source IDs and event dates first, then add only the attributes needed for analysis. A fact row must mean one thing. Don't join independent event tables into a single flattened table.

| Curated table | Grain | Source | Main dimensions/keys | Null and cleaning policy |
|---|---|---|---|---|
| `FactLikes` | One row per `likes.id` | `likes` | LikeID, LikerProfileID, StatusID, CreatedDate | Preserve nullable event date/deleted date; validate non-null status/profile references; flag soft-deleted likes rather than deleting them in staging. |
| `FactComments` | One row per `comments.id` | `comments` | CommentID, CommenterProfileID, StatusID, CreatedDate | Keep nullable comment text out of the basic fact; `user_id` may be null; status/profile FKs should be validated. |
| `FactMedia` | One row per `media.id` | `media` | MediaID, StatusID nullable, OwnerProfileID nullable, UploaderUserID nullable, CreatedDate | Keep media whose status/profile is null; use unmatched-FK checks; treat size/mime as nullable. Exclude key/hash/metadata detail unless needed. |
| `FactFollows` | One row per directed row in `followers` | `followers` | FollowRecordID, FollowerProfileID, FollowedProfileID, CreatedDate | Validate unique `(profile_id, following_id)`; flag self-follows or invalid endpoints for QA, don't silently remove. |
| `FactBookmarks` | One row per bookmark | `bookmarks` | BookmarkID, ProfileID, StatusID, CreatedDate | Validate unique `(status_id, profile_id)`; preserve nullable timestamps. |
| `BridgeStatusHashtag` | One row per status–hashtag pair | `status_hashtags` | StatusID, HashtagID; optional bridge row ID/profile | Validate unique `(status_id, hashtag_id)` and both endpoints; keep nullable bridge profile ID. |
| `FactMentions` | One row per mention | `mentions` | MentionID, StatusID, MentionedProfileID, CreatedDate | Keep deleted rows and flag `deleted_at`; validate non-null status/profile FKs. |
| `FactStoryViews` | One row per story-view event | `story_views` | StoryViewID, StoryID, ViewerProfileID, CreatedDate | Validate story/profile references; don't infer missing views from stored story counters. |
| `FactNotifications` | One row per notification | `notifications` | NotificationID, RecipientProfileID, optional ActorProfileID, ItemType/ItemID, CreatedDate, ReadAt | Actor/item/read time can be null; keep `ItemType` beside `ItemID`; don't join polymorphic ItemID directly to status. |
| `FactAccountLogs` | One row per account log | `account_logs` | AccountLogID, UserID, action/type, CreatedDate | Use only needed actions/types; exclude IP, user-agent and message payloads; ItemID is polymorphic with ItemType. |
| `FactWebSocketUsage` | One row per statistics entry | `websockets_statistics_entries` | EntryID, AppID, count metrics, CreatedDate | Counts should be numeric and non-negative; keep null timestamps as unknown, not a fake date. |

### Additional fact domains (phase 2, after core model works)

- **Moderation:** `FactReports` from `reports`, `FactReportComments`, `FactReportLogs`, `FactModLogs`. Use separate reporter/reported/commenter/moderator roles, and keep free-text messages out unless required.
- **Operations:** `FactJobs`, `FactFailedJobs`, `FactImports` from `import_datas` and `import_jobs`. Check timestamp formats carefully: `jobs.created_at`, `available_at`, `reserved_at`, and `sessions.last_activity` are integer epoch values, unlike the timestamp columns in most tables. Confirm whether values are seconds or milliseconds before conversion.
- **Communication:** `FactDirectMessages`, `FactContacts`, with sender/recipient/user roles. Don't expose message bodies by default.
- **Discovery:** `DimDiscoverCategory` and `BridgeDiscoverCategoryHashtag`; validate both referenced keys. `DimInstance` can support domain-level reporting if the source's domain relationships are validated.
- **Security:** only add `FactUserDevices`, `FactSessions`, or OAuth-derived summaries if there is a legitimate analytics question and the projection excludes secrets, tokens, session payloads, IP addresses, and fingerprints.

Do not build all 54 tables into separate dimensions/facts automatically. Some tables are operational/security entities, mapping tables, or configuration metadata; model them only when there's a defined analytics question.

## 8. Merge and expand safely

Use Merge Queries for a specific purpose, not just because two tables share a similarly named field.

1. Before a merge, make sure both join keys have the same data type and same semantic ID domain.
2. Confirm the lookup side is unique on the join key.
3. Choose **Left Outer** when retaining all rows from the primary event table is important.
4. Expand only the columns needed (usually a key/role or a handful of descriptive fields).
5. Compare row count before and after expanding. A many-to-one lookup should not multiply rows. If it does, diagnose duplicate lookup keys first.
6. Add a QA query using a **Left Anti** join to find rows in the fact with no matching lookup.
7. Do not merge `likes`, `comments`, `media`, or `followers` directly to each other. That produces fan-out (e.g., multiple likes × comments × media for one post) and inflates metrics.

Examples of justified merges:

- Merge `profiles` to `users` using `profiles.user_id = users.id` to enrich a profile with selected safe account attributes. Use a left outer join so remote profiles with null `user_id` remain.
- Merge `likes` to `statuses` using `likes.status_id = statuses.id` only if you explicitly need author/place attributes on the like event. Expand only `profile_id` (status author) and `place_id`. If `DimStatus` will supply status filtering and you have an unambiguous relationship path, keep this merge out of the fact to avoid duplicate columns.
- Do not merge `notifications.item_id` to statuses without first restricting by a validated `item_type`.

## 9. Keys and identity: prevent cross-entity collisions

Different tables may legitimately have the same integer primary-key value. That isn't a collision: `users.id = 15` and `profiles.id = 15` are different key domains. Never join them simply because the numbers look equal.

Correct user/profile join: `profiles.user_id` → `users.id`. The reverse association `users.profile_id` → `profiles.id` should be used as an independent consistency check. A remote profile can have `profiles.user_id = null` without being invalid.

For every dimension key:

- Check non-null count = row count for required keys.
- Check distinct count = row count.
- Check data type matches each related foreign key.

For every foreign key:

- Separate nullable from mandatory keys based on `schema.md`.
- Use a left-anti merge to list non-null FK values that have no parent row.
- Don't map an unknown/null key to `0` unless `0` is a deliberately reserved surrogate key and the dimension includes a corresponding Unknown row. The initial design should preserve null source IDs.

**Schema nuance:** the provided relationship list suggests `followers.id → follow_requests.follower_id`, but this is semantically suspicious: `followers.id` identifies a row in the follow-edge table, while `follow_requests.follower_id` represents a profile. For the generated data and semantic model, validate `follow_requests.follower_id` and `following_id` against `profiles.id`. Record this as a documented schema-relationship correction rather than silently treating the original diagram as authoritative.

## 10. Relationships: finish only after the curated queries are clean

Open **Model view → Manage relationships → New**. Do not accept every auto-detected relationship blindly.

Recommended baseline:

- `DimEventDate[Date]` → each event fact's `CreatedDate`: one-to-many, single direction.
- `DimPostDate[Date]` → `DimStatus[CreatedDate]`: one-to-many, single direction. Using a separate post-date role avoids an alternate active path to facts that already have event-date relationships.
- `DimProfile[ProfileID]` → `DimStatus[AuthorProfileID]`: one-to-many, single direction.
- `DimStatus[StatusID]` → `FactLikes[StatusID]`, `FactComments[StatusID]`, `FactMedia[StatusID]`, `FactBookmarks[StatusID]`, `FactMentions[StatusID]`, and `BridgeStatusHashtag[StatusID]`: one-to-many, single direction. For nullable fact keys, unmatched/blank rows must be understood, not discarded.
- `DimHashtag[HashtagID]` → `BridgeStatusHashtag[HashtagID]`: one-to-many, single direction.
- Role-playing profile dimensions → their matching fact role fields (liker/commenter/follower/followed/bookmarker/mentioned/story viewer/notification actor/recipient): one-to-many, single direction.
- `DimUser[UserID]` → `FactAccountLogs[UserID]`, plus `FactMedia[UploaderUserID]` if that role is modeled.
- `DimPlace[PlaceID]` → `DimStatus[PlaceID]` only if this doesn't create ambiguous filtering with the selected date/fact relationships. If unsure, expose PlaceID directly on the relevant facts, or add the place relationship only after testing the complete path.
- `DimStory[StoryID]` → `FactStoryViews[StoryID]`: one-to-many, single direction; use a story-viewer profile dimension for the viewer role.

Avoid one-to-one and bidirectional relationships unless a measured reporting requirement requires them. In particular, don't keep a separate one-row-per-status `FactPostMetrics` table linked 1:1 to `DimStatus` in the initial design. Put the source's current counters on `DimStatus` and create explicitly named measures over them; if a historical snapshot fact is later added, make its grain one status per snapshot date. Power BI one-to-one relationships always filter both directions and can introduce ambiguity.

### Hashtag filtering caveat

`BridgeStatusHashtag` is a many-to-many bridge between statuses and hashtags. With single-direction relationships, a hashtag selection filters the bridge but doesn't automatically propagate backward to `DimStatus` and then into every event fact. Don't solve this by enabling Both on every relationship. First confirm whether the required report only counts status–hashtag associations; for measures that need to filter status/event facts by hashtag, use a dedicated, tested bridge-aware DAX measure or a tightly scoped filtering design in the modeling phase.

## 11. Measure semantics: event counts are not stored counters

- Total posts: count statuses (`DimStatus` row count or distinct StatusID), subject to the chosen soft-delete rule.
- Like events: count rows in `FactLikes`, with the rule for `deleted_at` explicitly stated.
- Stored likes: sum `statuses.likes_count` once per status. Don't sum after joining to likes/comments/media events.
- Comment events: count rows in `FactComments`.
- Follow relationships: count valid rows in `FactFollows`; do not sum stored profile follower counts and call that unique users.
- Story view events: count rows in `FactStoryViews`; keep separate from `stories.view_count`.
- Notifications: count notification rows. Read notifications are rows with non-null `read_at`; do not replace null `read_at` with false dates.

Stored counters on profiles/statuses are snapshots from a source row, while event facts are record counts. Name them separately (for example `StoredLikes` vs `LikeEvents`) and document soft-delete treatment. Do not expect the two metrics to match perfectly without a source contract that guarantees reconciliation.

## 12. Final QA checklist

Before **Close & Apply**, verify:

- [ ] All 54 staging queries point to their assigned native format; no table is duplicated in another file format.
- [ ] Staging table row counts match `metadata/row_counts.csv`.
- [ ] All required primary keys are non-null and unique.
- [ ] Nullable foreign keys are kept null; non-null foreign keys are checked for unmatched parents.
- [ ] The ODBC numeric ID fields no longer arrive as Binary; textual IDs remain text.
- [ ] No blanket Replace Nulls or Remove Errors step was used without a documented rule.
- [ ] Blank text and null text have only been equated where business meaning supports it.
- [ ] Created/updated/deleted timestamps are not fabricated; epoch fields have an explicitly validated unit/time zone.
- [ ] Left outer merges retain the expected row count; expanding lookups doesn't multiply fact rows.
- [ ] Each curated dimension has a unique key and one row per entity.
- [ ] Each fact has one declared grain and independent event tables have not been merged together.
- [ ] Role-playing profile and date dimensions are used where a fact has multiple roles or dates.
- [ ] Relationships are reviewed manually; no unwanted many-to-many or ambiguous active paths remain.
- [ ] Sensitive credentials, tokens, private keys, session payloads, IP addresses and device fingerprints are not loaded into report-facing tables.
- [ ] Test totals for a few known source IDs match staging records.

Only after these checks pass should you build report visuals and optimize model layout.

## 13. Suggested learning sequence

1. Clean and validate `stg_users`, `stg_profiles`, `stg_statuses` and the `stg_` ODBC sources.
2. Build `DimUser`, `DimProfile`, `DimStatus`, `DimHashtag`, and `DimPlace`.
3. Build `DimEventDate` and `DimPostDate`.
4. Build only `FactLikes`, `FactComments`, `FactMedia`, and `FactFollows` first.
5. Validate relationships and totals before adding bookmarks, mentions, stories and notifications.
6. Add the `BridgeStatusHashtag` and document how hashtag filters should affect content metrics.
7. Add operations/moderation/security domains only when there is a clear question they answer.

## Microsoft references

- [Power Query best practices](https://learn.microsoft.com/en-us/power-query/best-practices)
- [Power Query data profiling tools](https://learn.microsoft.com/en-us/power-query/data-profiling-tools)
- [Dealing with errors in Power Query](https://learn.microsoft.com/en-us/power-query/dealing-with-errors)
- [Query folding guidance](https://learn.microsoft.com/en-us/power-bi/guidance/power-query-folding)
- [Star schema and Power BI semantic models](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [One-to-one relationship guidance](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-one-to-one)
- [Bi-directional relationship guidance](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-bidirectional-filtering)
- [Referencing queries in Power Query](https://learn.microsoft.com/en-us/power-bi/guidance/power-query-referenced-queries)


## Executable engagement implementation

The [Egypt source → Silver → galaxy implementation](egypt-engagement-implementation.md) specifies the current executable build, timestamp/identity validation, exact grains, quarantine behavior and Power BI relationship plan. Existing manual guides remain reference workflows; the new JSONL build does not automatically migrate the saved Power BI model.
