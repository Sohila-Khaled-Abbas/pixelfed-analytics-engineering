# PixelFed Analytics Engineering — Build Dimensions and Facts in Power Query

**Scope:** This guide covers only the curated dimensional layer: turning the 54 `stg_` source queries into reusable dimension, fact, and bridge queries for a Power BI galaxy model. It does not cover source-format import, TMDL scripts, DAX measures, or report design.

**Source contract:** the supplied PixelFed MySQL schema in `schema.md`.

**Landing zone:** `D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing`.

**How to use this guide:** perform every step in Power BI Desktop → **Transform data**. Use the UI for standard shaping operations. Open **Advanced Editor** only when you need to inspect or adjust a transformation that the UI created. This is a procedural guide, not a set of code scripts.

---

## 1. The target: one coherent galaxy, not one giant flat table

A galaxy model is a group of related stars: multiple fact tables at their own grains share conformed dimensions. Do not merge likes, comments, media, bookmarks, follows and posts into one wide table. A post may have many likes, many comments and several media records; joining those events together multiplies rows and inflates counts.

Build a **Core Content & Engagement** galaxy first. Add operational/moderation subject areas only after the core passes its validation checks.

### Core dimensions

| Query to create | One row per | Main source | Purpose |
|---|---|---|---|
| `DimDate` | Calendar date | Derived from relevant date columns | Common date filtering for events |
| `DimUser` | `users.id` | `stg_users` | Account-level attributes; no credentials |
| `DimProfile` | `profiles.id` | `stg_profiles` | Profile identity and reporting attributes |
| `DimAuthorProfile` | Profile | Reference to `DimProfile` | Profile in the author role |
| `DimLikerProfile` | Profile | Reference to `DimProfile` | Profile in the liker role |
| `DimCommenterProfile` | Profile | Reference to `DimProfile` | Profile in the commenter role |
| `DimMediaOwnerProfile` | Profile | Reference to `DimProfile` | Owner of a media record |
| `DimFollowerProfile` | Profile | Reference to `DimProfile` | Source/follower side of a follow edge |
| `DimFollowedProfile` | Profile | Reference to `DimProfile` | Target/followed side of a follow edge |
| `DimMentionedProfile` | Profile | Reference to `DimProfile` | Mentioned profile |
| `DimBookmarkingProfile` | Profile | Reference to `DimProfile` | Profile that created a bookmark |
| `DimStoryViewerProfile` | Profile | Reference to `DimProfile` | Profile viewing a story |
| `DimNotificationRecipientProfile` | Profile | Reference to `DimProfile` | Notification recipient |
| `DimNotificationActorProfile` | Profile | Reference to `DimProfile` | Profile that triggered a notification |
| `DimStatus` | `statuses.id` | `stg_statuses` | Post identity, type, visibility and other descriptors |
| `DimHashtag` | `hashtags.id` | `stg_hashtags` | Hashtag attributes |
| `DimPlace` | `places.id` | `stg_places` | Place attributes |
| `DimStory` | `stories.id` | `stg_stories` | Story attributes |
| `DimApp` | Distinct `app_id` | Derived from WebSocket statistics | App filter for usage statistics, if this subject area is added |

Role-playing profile queries intentionally contain the same profile rows under different names. Their purpose is semantic clarity: a commenter and a post author are different roles even if they happen to be the same person. Create only the roles needed by your chosen fact tables.

### Core facts and bridge

| Query to create | Required grain | Main source | Key fields to retain |
|---|---|---|---|
| `FactLikes` | One row per row in `likes` | `stg_likes` | Like ID, liker profile ID, status ID, created/deleted dates, flagged |
| `FactComments` | One row per row in `comments` | `stg_comments` | Comment ID, commenter profile ID, optional user ID, status ID, created date, remote flag |
| `FactMedia` | One row per row in `media` | `stg_media` | Media ID, optional status ID, profile ID, optional user ID, created/deleted dates, MIME, size, orientation, flags |
| `FactFollows` | One row per directed follow relation | `stg_followers` | Follow ID, follower profile ID, followed profile ID, created date, local flags |
| `FactBookmarks` | One row per bookmark | `stg_bookmarks` | Bookmark ID, status ID, bookmarking profile ID, created date |
| `BridgeStatusHashtag` | One row per status–hashtag association | `stg_status_hashtags` | Status ID, hashtag ID, optional profile ID, visibility, created date |
| `FactMentions` | One row per mention | `stg_mentions` | Mention ID, status ID, mentioned profile ID, created/deleted dates, local flag |
| `FactStoryViews` | One row per story-view record | `stg_story_views` | View ID, story ID, viewer profile ID, created date |
| `FactNotifications` | One row per notification | `stg_notifications` | Notification ID, recipient profile ID, optional actor ID, item type/ID, action, created/read/deleted dates |
| `FactAccountLogs` | One row per account log | `stg_account_logs` | Log ID, user ID, action, created date, item type/ID if useful |
| `FactWebSocketUsage` | One row per WebSocket statistics record | `stg_websockets_statistics_entries` | Entry ID, app ID, date, peak connections, WebSocket-message count, API-message count |

**Important choice about stored counters:** `statuses.likes_count`, `statuses.reblogs_count` and `statuses.reply_count` are counters stored on the post entity. The schema does not provide a separate snapshot timestamp or historical counter table. Retain them as clearly labelled source-reported counters on `DimStatus` for this project, and create explicit measures over the one-row-per-status dimension. Do not call these historical engagement events and do not expect them to equal the counts of `FactLikes` or `FactComments`. If you later capture dated snapshots, model those snapshots as a separate fact table with an explicit snapshot date.

`stories.view_count` and `stories.comment_count` have the same limitation: they are source counters, whereas `FactStoryViews` is an event table.

---

## 2. Before creating curated queries: prepare the query workspace

### Step 2.1 — Confirm staging names

In Power Query Editor, confirm that each source query is named `stg_<schema_table>`—for example `stg_users`, `stg_profiles`, `stg_statuses`, `stg_likes` and `stg_status_hashtags`. Keep these queries as the faithful source layer; do not apply business-specific joins or aggregation to them.

### Step 2.2 — Create query groups

In the Queries pane, create these groups and move queries into them:

- **00 Parameters** — source path or other connection parameters.
- **01 Staging** — the 54 `stg_` source queries.
- **02 Dimensions** — all `Dim…` queries, including role-playing dimensions.
- **03 Facts and Bridges** — all `Fact…` and `Bridge…` queries.
- **99 QA** — temporary checks, duplicate-key investigations and orphan-key reports.

Use meaningful names and add query descriptions where useful. For example, describe `FactLikes` as “One row per like-event record; `profile_id` is the liker, and `status_id` identifies the liked status.”

### Step 2.3 — Keep staging reproducible

- Right-click each curated query's source in the Queries pane and choose **Reference**, not **Duplicate**. Reference starts a new query based on the output of the referenced query while preserving the staged source logic.
- Disable load for the `stg_` queries after you have confirmed that the curated references work. The curated dimensions and facts should be the reporting tables loaded to the model.
- A reference is not a guaranteed in-memory cache. Several referenced queries may evaluate their upstream source during refresh. Keep the transformations lean and avoid expensive, repeated merges where possible.
- Keep the original key columns in staging, even if a curated query renames them. You need those source keys for reconciliation and troubleshooting.

### Step 2.4 — Profile before shaping

On the **View** ribbon, enable **Column quality**, **Column distribution** and **Column profile**. Change profiling from the top 1,000 rows to the entire dataset for validation where practical.

For every source key, check blank values, errors, distinct count and duplicate count. Do not automatically choose **Remove duplicates** just because a key is duplicated. First determine whether the duplication violates the documented grain or whether the data is legitimately many-to-many.

### Step 2.5 — Standardize types before model relationships

- Numeric source keys and numeric foreign keys: **Whole Number** (`Int64`), when the SQLite/ODBC fix has returned a readable numeric value.
- Text-based keys: **Text**; examples include OAuth token IDs and session IDs.
- Binary values: inspect the source and connector. Never convert arbitrary binary bytes to a number just because the column name ends in `_id`.
- Timestamps: use Date/Time consistently in staging, then create date-only key columns for calendar relationships in curated facts. Know whether the source timestamp represents UTC before applying a timezone conversion.
- Flags: retain source `0`/`1` values in staging. In curated queries, convert to True/False only after checking that all non-null values are 0 or 1 and that null handling is explicit.
- JSON and long text: leave unexpanded in staging until there is a defined reporting question. Exclude credential-like or high-volume payload fields from curated tables by default.

For SQLite ODBC ID fields previously returned as Binary, complete the source projection/type fix first. If Power Query still sees Binary after the source step, stop and inspect the ODBC driver and source values before building dimensions on that field.

---

## 3. Build dimensions first

For each dimension, use **Reference** on the stated staging query. Rename the new query to the dimension name, select only the approved columns, rename keys to make their meaning explicit, set types, apply justified text cleanup, then validate key uniqueness.

### Step 3.1 — `DimUser`

**Source:** `stg_users`. **Grain:** one row per `users.id`.

1. Right-click `stg_users` → **Reference**. Rename the result `DimUser`.
2. Use **Choose Columns**; keep only `id`, `name`, `username`, `status`, `language`, `is_admin`, `email_verified_at`, `created_at` and `deleted_at`.
3. Rename `id` to `UserID`; use descriptive names for other fields if they will appear in the report.
4. Set `UserID` to Whole Number. Set text attributes to Text and timestamp attributes to Date/Time. Treat `is_admin` as a flag only after checking its values.
5. Trim and clean `username`, `name`, `status` and `language` only if profiling shows unwanted whitespace or control characters. Do not lowercase display names automatically. If you standardize usernames, apply the same rule consistently to both sides of any later text-key comparison.
6. Do not keep `password`, `remember_token`, `2fa_secret`, backup codes, or tokens in this dimension. Do not import email by default; include it only if an approved analytic need exists.
7. Validate that `UserID` is non-null and unique. Investigate duplicate IDs instead of silently removing them.

**Expected result:** a narrow account dimension with one row per user and no authentication secrets.

### Step 3.2 — `DimProfile`

**Source:** `stg_profiles`. **Grain:** one row per `profiles.id`.

1. Reference `stg_profiles` and name the query `DimProfile`.
2. Keep `id`, `user_id`, `domain`, `username`, `status`, `name`, `unlisted`, `cw`, `location`, `profile_layout`, `post_layout`, `is_private`, `created_at`, `deleted_at`, `is_suggestable`, `status_count`, `followers_count` and `following_count`.
3. Rename `id` to `ProfileID` and `user_id` to `UserID`. Retain `UserID` as a reference attribute; do not merge the whole users table into profiles unless you validate the relationship cardinality first.
4. Set profile IDs and counts to Whole Number; set text columns to Text; set timestamps to Date/Time; treat flags as Boolean only after validating them.
5. Review `location` before exposing it in report visuals. Do not bring `private_key`, `public_key`, security identifiers or unnecessary federation URLs into the curated dimension.
6. Validate `ProfileID` uniqueness and non-nullness. Check whether `UserID` can be null or repeat; its behavior must follow the source contract, not an assumption that user and profile are always one-to-one.

**Expected result:** one narrow row per profile. Keep `DimUser` and `DimProfile` separate in this first version because the source schema contains links in both directions and does not establish a simple one-to-one user/profile mapping for every row.

### Step 3.3 — Role-playing profile dimensions

Create these only after `DimProfile` passes its uniqueness check. For each role, right-click `DimProfile` → **Reference** and rename the new query.

| New query | Rename the key to | Where the role is used |
|---|---|---|
| `DimAuthorProfile` | `AuthorProfileID` | `DimStatus` author profile |
| `DimLikerProfile` | `LikerProfileID` | `FactLikes` |
| `DimCommenterProfile` | `CommenterProfileID` | `FactComments` |
| `DimMediaOwnerProfile` | `MediaOwnerProfileID` | `FactMedia` |
| `DimFollowerProfile` | `FollowerProfileID` | `FactFollows` source side |
| `DimFollowedProfile` | `FollowedProfileID` | `FactFollows` target side |
| `DimBookmarkingProfile` | `BookmarkingProfileID` | `FactBookmarks` |
| `DimMentionedProfile` | `MentionedProfileID` | `FactMentions` |
| `DimStoryViewerProfile` | `StoryViewerProfileID` | `FactStoryViews` |
| `DimNotificationRecipientProfile` | `NotificationRecipientProfileID` | `FactNotifications` recipient |
| `DimNotificationActorProfile` | `NotificationActorProfileID` | `FactNotifications` actor |

For each referenced query, keep the same profile attributes but rename `ProfileID` to the role-specific key. Do not append these role dimensions together. They represent the same profile entities under distinct roles. If you are not using a role in a fact, you do not need to load that role dimension yet. In this first version, treat `DimProfile` as the reusable template query and disable its load unless you also have a fact that uses the generic profile role; load only the role dimensions that participate in the model. This avoids leaving an unused, disconnected `DimProfile` table in the field list.

### Step 3.4 — `DimStatus`

**Source:** `stg_statuses`. **Grain:** one row per `statuses.id`.

1. Reference `stg_statuses`; rename it `DimStatus`.
2. Keep `id`, `profile_id`, `type`, `is_nsfw`, `scope`, `visibility`, `reply`, `language`, `created_at`, `deleted_at`, `place_id`, `comments_disabled`, and optionally `in_reply_to_id`, `reblog_of_id`, `conversation_id` and `local` if the report needs thread, reblog or local/public analysis.
3. Rename `id` to `StatusID`, `profile_id` to `AuthorProfileID`, and `place_id` to `PlaceID`. Keep the source timestamp as `CreatedAt`; also create a separate Date-typed `CreatedDate` column from it for the status-created-date role. Rename other flags and dates descriptively as needed.
4. Set `StatusID` and numeric key columns to Whole Number, types/visibility/language to Text, and the original timestamps to Date/Time. Keep the original creation timestamp as `CreatedAt`, then add a separate date-only column named `CreatedDate` using **Add Column/Transform → Date → Date Only**. Do not replace the original timestamp. Set flags to Boolean only after validating their values.
5. Keep `likes_count`, `reblogs_count` and `reply_count` only if you intend to report the source-stored counters. These are counters recorded on the post row, not like/reblog/comment event counts. Give them explicit, clear names (such as stored likes) and use explicit measures rather than implicit summation in visuals.
6. Exclude `caption`, `rendered`, `entities`, URLs and other large/free-text content unless a defined analysis specifically needs them. Never bring secret or private-key fields into this dimension.
7. Validate `StatusID` is non-null and unique. Check that non-null `AuthorProfileID` values exist in `DimProfile`. Null `PlaceID` is allowed because the schema marks `statuses.place_id` nullable.

### Step 3.5 — `DimHashtag`

**Source:** `stg_hashtags`. **Grain:** one row per hashtag.

1. Reference `stg_hashtags` and rename `id` to `HashtagID`.
2. Keep `name`, `slug`, `is_nsfw`, `is_banned`, `created_at` and `updated_at`.
3. Set ID to Whole Number; name and slug to Text; dates to Date/Time; flags to validated Boolean.
4. Validate that `HashtagID`, `name` and `slug` follow the uniqueness rules in the schema. Clean leading/trailing spaces if required, but do not alter hashtag names/slug casing without defining a consistent business rule.

### Step 3.6 — `DimPlace`

**Source:** `stg_places`. **Grain:** one row per place.

1. Reference `stg_places`; rename `id` to `PlaceID`.
2. Keep `slug`, `name`, `country`, `lat` and `long`. Keep aliases only if a report actually needs them.
3. Set coordinates to Decimal Number (not Whole Number), IDs to Whole Number and labels to Text.
4. Validate `PlaceID` uniqueness and profile empty coordinate pairs separately. Do not replace missing coordinates with zero; zero is a valid geographic coordinate.

### Step 3.7 — `DimStory`

**Source:** `stg_stories`. **Grain:** one row per `stories.id`.

1. Reference `stg_stories`; keep `id`, `profile_id`, `type`, `mime`, `public`, `local`, `expires_at`, `created_at`, and optionally `duration`, `size`, `view_count` and `comment_count`.
2. Rename `id` to `StoryID` and `profile_id` to `StoryOwnerProfileID`.
3. Set IDs, sizes and counts to Whole Number; text attributes to Text; timestamps to Date/Time; flags to validated Boolean.
4. Exclude paths, CDN URLs, JSON story payloads and other large content fields by default.
5. Treat `view_count` and `comment_count` as stored source counters; do not assume they equal rows in `FactStoryViews` or comments.

### Step 3.8 — `DimApp` (optional)

Create this only if you include `FactWebSocketUsage`. Reference `stg_websockets_statistics_entries`, keep only `app_id`, remove blank app IDs if they are invalid by the business definition, and remove duplicates on `app_id` after checking the distinct values. Rename it `DimApp` and its key `AppID`. Every `FactWebSocketUsage[AppID]` must match one row in this dimension or be handled as an explicit unknown/blank app.

### Step 3.9 — `DimDate`

The source schema has timestamps but no calendar table. Create a continuous date dimension so reports can show dates with no events.

1. In Power Query, create a Blank Query and name it `DimDate`.
2. Use the Advanced Editor only for this date-spine query: a continuous range is best represented by an M date-list operation rather than manually typing rows. The start and end boundaries should be driven by the minimum and maximum valid dates across the date columns you plan to analyze; do not depend on whichever table happens to be shortest.
3. Convert the list to a table and name the date column `Date`. Make it a Date type, not Date/Time.
4. Add `DateKey` as an integer in YYYYMMDD form, plus Year, Quarter, MonthNumber, MonthName, YearMonth, and DayOfWeek attributes using the Date transformations on the ribbon where available.
5. Check that every calendar day between the minimum and maximum dates is present, no `Date` is blank, and each date occurs once.
6. Later in Model view, mark it as the date table and sort MonthName by MonthNumber and YearMonth by a numeric month-start/date key.

Use `DimDate` as the shared **event-created date** dimension and connect it directly to the created-date-only column on each event fact. Do not connect this same `DimDate` to `DimStatus[CreatedAt]` while it also filters facts that relate to `DimStatus`; that can create more than one active path to an interaction fact. Instead, create a reference to `DimDate` named `DimStatusCreatedDate` and relate that role to `DimStatus[CreatedDate]` in Model view. If you want to analyze story creation separately from story-view events, create `DimStoryCreatedDate` as another role. Likewise, if read date must be independently slicable from notification created date, create `DimNotificationReadDate` or deliberately use an inactive relationship and suitable DAX later. Do not create many confusing active paths by connecting several date roles to the same fact without a plan.

---

## 4. Build the core facts one at a time

For a fact table, Reference its own staging query; keep the source event grain intact; retain its natural/source key and foreign keys; rename columns to express their role; set explicit types; and validate required columns. For every fact that has `created_at`, retain the full timestamp as `CreatedAt` and add a separate Date-typed `CreatedDate` via the ribbon. Relate `DimDate[Date]` to `CreatedDate`, not to a timestamp that contains a time component. Preserve `ReadAt`, `DeletedAt`, `UpdatedAt` and other timestamps separately when they are needed. Do not Group By, Remove Duplicates, or merge unrelated event tables as part of the initial fact build.

### Step 4.1 — `FactLikes`

**Source:** `stg_likes`. **Grain:** one row per source row in `likes`.

1. Reference the source and name the query `FactLikes`.
2. Keep `id`, `profile_id`, `status_id`, `flagged`, `created_at`, `updated_at` and `deleted_at`.
3. Rename them `LikeID`, `LikerProfileID`, `StatusID`, `Flagged`, `CreatedAt`, `UpdatedAt` and `DeletedAt`.
4. Use Whole Number for keys and flags; Date/Time for timestamps.
5. Do not remove deleted like rows. Keep `DeletedAt` so each measure can choose whether it counts all events or only non-deleted events.
6. Validate `LikeID` is unique and non-null. Also validate that the `(LikerProfileID, StatusID)` pair is unique per the source schema's unique index.
7. Check non-null `LikerProfileID` values against `DimProfile` and `StatusID` against `DimStatus`.

### Step 4.2 — `FactComments`

**Source:** `stg_comments`. **Grain:** one row per comment row.

1. Reference and name `FactComments`.
2. Keep `id`, `profile_id`, `user_id`, `status_id`, `is_remote`, `created_at`, `updated_at` and `rendered_at`. Only keep the actual comment text when a documented analysis needs it.
3. Rename `id` to `CommentID`, `profile_id` to `CommenterProfileID`, `user_id` to `UserID`, and `status_id` to `StatusID`.
4. Set IDs to Whole Number; timestamps to Date/Time; `is_remote` to a validated Boolean or Whole Number flag.
5. Leave nullable `UserID` values blank; do not replace them with zero. Don't automatically remove empty comment text: the schema allows `comment` to be nullable.
6. Validate `CommentID` uniqueness and non-nullness; check profile and status key matches. Keep each comment as an event row.

### Step 4.3 — `FactMedia`

**Source:** `stg_media`. **Grain:** one row per media record.

1. Reference and name `FactMedia`.
2. Keep `id`, `status_id`, `profile_id`, `user_id`, `is_nsfw`, `remote_media`, `mime`, `size`, `orientation`, `processed_at`, `created_at`, `updated_at` and `deleted_at`.
3. Rename keys `MediaID`, `StatusID`, `MediaOwnerProfileID` and `UploaderUserID`.
4. Set key fields to Whole Number. Set `size` to Whole Number, but profile its maximum first so it remains within Power BI's supported integer range. Use Date/Time for timestamps, Text for MIME/orientation, and validated Boolean flags.
5. Preserve blank `StatusID`, `MediaOwnerProfileID` and `UploaderUserID` values where the source allows null. Do not replace null keys with zero.
6. Exclude SHA hashes, storage paths, CDN/remote URLs, keys and raw metadata unless the report specifically needs them.
7. Validate `MediaID` uniqueness. Check non-null status and profile IDs against their dimensions; a nullable `StatusID` is not automatically an error.

### Step 4.4 — `FactFollows`

**Source:** `stg_followers`. **Grain:** one directed follow relation.

1. Reference and name `FactFollows`.
2. Keep `id`, `profile_id`, `following_id`, `local_profile`, `local_following`, `created_at` and `updated_at`.
3. Rename them `FollowID`, `FollowerProfileID`, `FollowedProfileID`, `LocalFollower`, `LocalFollowed`, `CreatedAt` and `UpdatedAt`.
4. Set IDs to Whole Number, timestamps to Date/Time, and local flags to validated Boolean.
5. Validate `FollowID` and the pair `(FollowerProfileID, FollowedProfileID)`. Check that both role keys exist in `DimProfile` and flag self-follows for review rather than silently deleting them.
6. Keep `follow_requests` separate: a request is not a completed follow. Do not use the unusual documented `followers.id → follow_requests.follower_id` relationship until the values and intended key domain have been verified.

### Step 4.5 — `FactBookmarks`

**Source:** `stg_bookmarks`. **Grain:** one bookmark row.

1. Reference and name `FactBookmarks`.
2. Keep `id`, `status_id`, `profile_id`, `created_at`, `updated_at`.
3. Rename to `BookmarkID`, `StatusID`, `BookmarkingProfileID`, `CreatedAt` and `UpdatedAt`.
4. Apply Whole Number to IDs and Date/Time to timestamps.
5. Validate primary-key uniqueness and the unique `(StatusID, BookmarkingProfileID)` pair. Check the status and profile keys against their dimensions.

### Step 4.6 — `BridgeStatusHashtag`

**Source:** `stg_status_hashtags`. **Grain:** one status–hashtag link row, not one post and not one hashtag.

1. Reference and name `BridgeStatusHashtag`.
2. Keep `id`, `status_id`, `hashtag_id`, `profile_id`, `status_visibility`, `created_at` and `updated_at`.
3. Rename keys to `StatusHashtagID`, `StatusID`, `HashtagID` and `ProfileID`.
4. Set keys to Whole Number, visibility to Text and timestamps to Date/Time.
5. Validate each link key and the unique `(StatusID, HashtagID)` pair. Check that status and hashtag keys exist in their dimensions; the source allows nullable `profile_id`.
6. Do not merge hashtag names onto every post or remove duplicates across all columns. This bridge preserves multiple hashtags per status. When measuring posts by hashtag, count distinct `StatusID`, not bridge rows, because one status may have several hashtags.

### Step 4.7 — `FactMentions`

**Source:** `stg_mentions`. **Grain:** one mention row.

1. Reference and name `FactMentions`.
2. Keep `id`, `status_id`, `profile_id`, `local`, `created_at`, `updated_at`, `deleted_at`.
3. Rename `id` to `MentionID`, `status_id` to `StatusID` and `profile_id` to `MentionedProfileID`.
4. Set IDs to Whole Number, local flag to validated Boolean and timestamps to Date/Time.
5. Validate unique `MentionID` and check the referenced status/profile keys. Retain deleted events with `DeletedAt` for transparent measure definitions.

### Step 4.8 — `FactStoryViews`

**Source:** `stg_story_views`. **Grain:** one story-view row.

1. Reference and name `FactStoryViews`.
2. Keep `id`, `story_id`, `profile_id`, `created_at` and `updated_at`.
3. Rename keys to `StoryViewID`, `StoryID` and `StoryViewerProfileID`.
4. Set keys to Whole Number and timestamps to Date/Time.
5. Validate unique `StoryViewID` and the unique `(StoryID, StoryViewerProfileID)` pair listed in the schema. Check both role keys against `DimStory` and `DimStoryViewerProfile`.

### Step 4.9 — `FactNotifications`

**Source:** `stg_notifications`. **Grain:** one notification row.

1. Reference and name `FactNotifications`.
2. Keep `id`, `profile_id`, `actor_id`, `item_id`, `item_type`, `action`, `created_at`, `read_at`, `updated_at` and `deleted_at`. Keep user-facing message fields only when specifically required.
3. Rename `id` to `NotificationID`, `profile_id` to `NotificationRecipientProfileID`, and `actor_id` to `NotificationActorProfileID`.
4. Set profile and item IDs to Whole Number, `item_type` and `action` to Text, and timestamps to Date/Time.
5. `actor_id` and `item_id` may be nullable. `item_id` is polymorphic: its target depends on `item_type`, so do not create a generic relationship to `DimStatus` or another dimension.
6. Validate notification ID uniqueness and profile role-key matches. Keep created and read timestamps separately; use only one active date relationship by default.

### Step 4.10 — `FactAccountLogs`

**Source:** `stg_account_logs`. **Grain:** one account-log record.

1. Reference and name `FactAccountLogs`.
2. Keep `id`, `user_id`, `item_id`, `item_type`, `action`, `created_at` and `updated_at` where needed.
3. Rename `id` to `AccountLogID`, `user_id` to `UserID`, and timestamps to consistent names.
4. Set IDs to Whole Number, action/type to Text and timestamps to Date/Time.
5. Exclude IP addresses, user-agent strings, raw messages and metadata by default. `item_id` plus `item_type` is polymorphic and must not be joined to a single entity without type-specific logic.
6. Validate log ID and non-null user-key matches. These records are sensitive operational data; keep reporting aggregated and access controlled.

### Step 4.11 — `FactWebSocketUsage` (optional operational star)

**Source:** `stg_websockets_statistics_entries`. **Grain:** one source statistics record.

1. Reference and name `FactWebSocketUsage`.
2. Keep `id`, `app_id`, `peak_connection_count`, `websocket_message_count`, `api_message_count`, `created_at` and `updated_at`.
3. Rename the key and metrics to descriptive names; use Whole Number for counts, Text for app ID and Date/Time for timestamps.
4. Validate `id` and inspect whether repeated app IDs are expected. If app-level filtering is valuable, build `DimApp` from the distinct set of app IDs and relate it to this fact. Do not create an app dimension if the field is empty or carries no useful variety.

---

## 5. Hand off the curated tables to the galaxy relationships

These relationships are created later in **Model view**, not by merging descriptive columns into Power Query facts. Add one relationship at a time and check that the dimension-side key is unique and both columns have compatible types. Keep cross-filter direction single from dimension to fact/bridge unless there is a documented reason otherwise.

| Dimension side (one) | Fact/bridge side (many) | Notes |
|---|---|---|
| `DimStatus[StatusID]` | `FactLikes[StatusID]`, `FactComments[StatusID]`, `FactMedia[StatusID]`, `FactBookmarks[StatusID]`, `FactMentions[StatusID]`, `BridgeStatusHashtag[StatusID]` | Keep nullable `FactMedia[StatusID]` rows; an unmatched/blank status is valid if the source allows it. |
| `DimAuthorProfile[AuthorProfileID]` | `DimStatus[AuthorProfileID]` | One author profile can author many statuses; this intentionally creates a snowflaked path from author profile → status → engagement facts. |
| `DimLikerProfile[LikerProfileID]` | `FactLikes[LikerProfileID]` | Profile role: person who liked the post. |
| `DimCommenterProfile[CommenterProfileID]` | `FactComments[CommenterProfileID]` | Profile role: person who commented. |
| `DimMediaOwnerProfile[MediaOwnerProfileID]` | `FactMedia[MediaOwnerProfileID]` | Media ownership role; may be blank if the schema permits. |
| `DimUser[UserID]` | `FactComments[UserID]`, `FactMedia[UploaderUserID]`, `FactAccountLogs[UserID]` | Only create each relationship if the source values match `users.id`; preserve nullable comment/media user IDs. |
| `DimFollowerProfile[FollowerProfileID]` | `FactFollows[FollowerProfileID]` | Source/initiator of the directed follow edge. |
| `DimFollowedProfile[FollowedProfileID]` | `FactFollows[FollowedProfileID]` | Target of the directed follow edge; first validate these values against `profiles.id`. |
| `DimBookmarkingProfile[BookmarkingProfileID]` | `FactBookmarks[BookmarkingProfileID]` | Person who bookmarked the status. |
| `DimHashtag[HashtagID]` | `BridgeStatusHashtag[HashtagID]` | Use the bridge for hashtag-to-status analysis. |
| `DimMentionedProfile[MentionedProfileID]` | `FactMentions[MentionedProfileID]` | Person named in the mention, not the post author. |
| `DimStory[StoryID]` | `FactStoryViews[StoryID]` | A story can have many view rows. |
| `DimStoryViewerProfile[StoryViewerProfileID]` | `FactStoryViews[StoryViewerProfileID]` | Person who viewed the story. |
| `DimNotificationRecipientProfile[NotificationRecipientProfileID]` | `FactNotifications[NotificationRecipientProfileID]` | Recipient role. |
| `DimNotificationActorProfile[NotificationActorProfileID]` | `FactNotifications[NotificationActorProfileID]` | Actor role; nullable actors must remain blank. |
| `DimApp[AppID]` | `FactWebSocketUsage[AppID]` | Optional; only if the usage subject area is included. |
| `DimDate[Date]` | Each event fact's created-date column | Use the event's own created date for event-volume trends. Create date-only columns in Power Query while retaining the full timestamp. |
| `DimStatusCreatedDate[Date]` | `DimStatus[CreatedDate]` | Separate date role to analyze content by post-created date without creating an ambiguous path through event-created dates. `DimStatusCreatedDate` is a reference to `DimDate`. |

Do not connect `DimProfile` as a generic extra path as well as all its role-playing copies. In this core model, use the specific role dimensions shown above; keep the base `DimProfile` as a non-loaded template query unless it has a separate, clear reporting role. Also do not relate polymorphic `item_id` or `object_id` fields directly to `DimStatus`: the correct target depends on `item_type`/`object_type`.

---

## 5. Data shaping rules to use consistently

### Select columns early, expand narrowly

Use **Choose Columns** near the beginning of each curated query. This reduces model size and makes the intended contract clear. When expanding a merged table, select only the specific key or attributes that are required; avoid expanding all columns and removing most of them afterwards.

### Avoid unnecessary merges

For the core galaxy, keep foreign keys in the facts and create relationships in Model view. Do not merge all profile/status attributes onto every event table just to make visuals easier. Merge only when a query needs to derive a key or when you deliberately create a denormalized dimension.

A safe exception is enriching an event with one parent attribute through a lookup that has a validated unique key. If you merge a fact to `stg_statuses`, ensure `stg_statuses[id]` is unique before merging, use a left outer join if events with missing parents should be retained, expand only the needed attributes, and verify that the row count did not increase. If it did, you likely joined to a non-unique lookup or introduced fan-out.

### Do not aggregate raw facts in Power Query unless the grain calls for it

- `FactLikes` stays one row per like.
- `FactComments` stays one row per comment.
- `FactMedia` stays one row per media item.
- `FactFollows` stays one row per directed follow relation.
- `BridgeStatusHashtag` stays one row per status–hashtag pair.

Use Group By only for a separate, explicitly aggregated table with a stated grain. Do not overwrite the atomic fact query with a summarized version.

### Don't use Remove Duplicates to silence quality failures

For each dimension, inspect its natural key using the column profile, sort/filter for repeated keys, and understand the cause before changing rows. For bridges, check the expected composite uniqueness constraint. `Remove Duplicates` is appropriate only when your documented business key says the duplicates are redundant and you understand which row should survive.

### Nulls, errors and soft deletes

- Preserve null foreign keys when the schema says they are nullable; don't replace them with zero.
- Don't use **Remove Errors** as a blanket cleanup step. Filter error rows into a temporary QA query or inspect them and correct the source/type logic.
- Preserve `deleted_at` in facts/dimensions where available. Create explicit reporting rules for including/excluding deleted rows; don't erase the history during data preparation.
- Keep original date/time columns until the curated query is validated. Add separate date-only relationship columns rather than overwriting the timestamp when the exact event time might later matter.

### Prefer repeatable transformations

- Use the ribbon to create clear steps such as Choose Columns, Rename Columns, Change Type, Trim, Clean and Merge Queries. Power Query records these as M steps for you.
- Rename steps using meaningful names such as “Keep reporting columns”, “Set key and timestamp types”, or “Validate relationship keys”.
- Inspect Advanced Editor to understand generated M when a step behaves unexpectedly, but avoid editing long M definitions by hand until the UI-generated query works.
- Check whether the source step still supports query folding for ODBC/relational transformations. File sources such as CSV, JSON and Excel generally require Power Query to perform transformations locally, so keep projections narrow and avoid expensive row-by-row transformations where possible.
- Do not add `Table.Buffer` or other performance tricks by default. Measure refresh performance first; buffering can increase memory use or prevent folding.

Microsoft guidance: [Power Query best practices](https://learn.microsoft.com/power-query/best-practices), [Query folding guidance](https://learn.microsoft.com/power-bi/guidance/power-query-folding), and [Referencing queries](https://learn.microsoft.com/power-bi/guidance/power-query-referenced-queries).

---

## Learn what the GUI is writing in M (without replacing everything with hand-written code)

Power Query's ribbon actions generate M transformations. Learn to recognize the operation behind each UI action so you can troubleshoot it in Advanced Editor without having to rewrite entire queries. In this guide, use the UI to create these steps and inspect the generated M; no prebuilt script is required.

| Power Query action | M operation you will typically see | Best-practice use |
|---|---|---|
| Right-click query → **Reference** | A query reference | Start each curated table from a validated staging query. |
| **Choose Columns** | `Table.SelectColumns` | Keep only the columns required for the dimension or fact, early in the query. |
| **Rename** | `Table.RenameColumns` | Make source keys and roles explicit, such as `profile_id` becoming `LikerProfileID`. |
| **Change Type** | `Table.TransformColumnTypes` | Set types deliberately after checking source values. |
| **Transform → Format → Trim/Clean** | Text transformation steps such as `Text.Trim` and `Text.Clean` | Remove unwanted edge whitespace/control characters only from text fields where profiling justifies it. |
| **Merge Queries** | `Table.NestedJoin` | Use only for an intended lookup, with a unique key on the lookup side. |
| Expand merged table | `Table.ExpandTableColumn` | Expand only the required columns; compare row counts before and after the merge. |
| **Add Column → Date → Date Only** | A date extraction step, often using `Date.From` | Make a separate date relationship column while preserving the full timestamp. |
| **Group By** | `Table.Group` | Use for a separately named aggregate table only when the aggregate grain is explicitly defined. Do not replace the atomic event fact. |

When using Advanced Editor, edit or inspect one logical transformation at a time. Confirm the query preview after changes. Avoid unnecessary `Table.Buffer`, broad error-swallowing transformations, and manual rewrites of connector-generated source steps unless you understand the effect on query folding.

---

## 6. Create the role-playing dimensions without creating duplicate semantics

A role-playing dimension is a reference to the same underlying entity used for a different role in a fact. For example, a notification has a recipient and an actor; a follow has a follower and a followed profile.

For each role you need:

1. Right-click `DimProfile` and choose **Reference**.
2. Rename it with its role, such as `DimFollowerProfile`.
3. Keep the same selected profile attributes.
4. Rename `ProfileID` to the role-specific key.
5. Validate the role-specific key is still unique and has the same data type as the matching fact column.

Do not create every role in advance if you are not modeling that fact yet. A role dimension should have one clear relationship purpose and should not create multiple active paths between tables.

---

## 7. What to do with the remaining schema tables

Do not force all operational tables into the first content galaxy. Many are security, application-control or polymorphic structures; retain them in staging while the core model is being validated.

| Schema area | Tables | Recommendation for a later phase |
|---|---|---|
| Social requests and tags | `follow_requests`, `hashtag_follows`, `discover_categories`, `discover_category_hashtags` | Separate request/follow facts and category–hashtag bridge; validate key domains before relationships |
| Collections and circles | `circles`, `circle_profiles`, `collections`, `collection_items` | Dimensions and membership bridges; keep `object_id` polymorphic in `collection_items` and do not link it generically to statuses |
| Reports and moderation | `reports`, `report_comments`, `report_logs`, `mod_logs` | Separate fact tables with reporter, reported-profile and admin roles; omit message and metadata payloads unless necessary |
| Import/queue operations | `import_jobs`, `import_datas`, `jobs`, `failed_jobs` | Separate job and import-item facts. Convert epoch integer timestamps carefully; exclude payload and exception text |
| Editorial content | `newsroom`, `pages` | Curated publication/page dimensions or publication facts with limited metadata; exclude long body/content fields unless required |
| Profile extensions | `avatars`, `profile_sponsors`, `user_settings` | Merge one-to-one extensions only after key cardinality is verified. Avoid loading sponsor JSON or private settings by default |
| User interactions | `contacts`, `email_verifications`, `user_invites`, `user_devices`, `user_filters` | Include only approved workflow metrics. Exclude messages/responses, email and tokens, IPs, fingerprints and user-agent data |
| Auth/security | `oauth_access_tokens`, `oauth_auth_codes`, `oauth_clients`, `oauth_personal_access_clients`, `oauth_refresh_tokens`, `password_resets`, `sessions` | Keep out of the reporting model by default. Token, client-secret, reset-token, session payload and IP data are not appropriate analytics attributes |
| App/system metadata | `instances`, `migrations` | `DimInstance` can support federation-domain analysis if desired. `migrations` is deployment metadata and usually stays outside the report model |
| Activity stream | `activities` | Treat `to_id`, `from_id` and JSON `data` carefully; confirm their key domains and parse only fields needed for defined metrics |

Two schema cautions:

- The documented relationship `followers.id → follow_requests.follower_id` is unusual. Validate the actual values and intended key domain before creating the relationship; do not accept it solely because it appears in the relationship section.
- `collection_items.object_id`, `notifications.item_id`, account-log `item_id`, and similar fields are polymorphic. Their target entity depends on a companion type column. Do not create a generic foreign-key relationship from the ID alone.

---

## 8. Validate every curated query before loading it

Create temporary queries in `99 QA` or use profiling tools. Do not load them to the semantic model.

| Validation | Expected result | If it fails |
|---|---|---|
| Dimension key completeness | Required dimension key has no nulls | Inspect source and type conversion; don't invent zero IDs |
| Dimension key uniqueness | One row per dimension key | Filter duplicates and investigate the source/business key |
| Fact grain | One row per declared event/key | Check the source key and ensure no accidental merge expanded rows |
| Fact foreign-key coverage | Non-null foreign keys match their dimensions | Check the domain, type, whitespace and whether the source allows missing parents |
| Join row-count check | A lookup merge does not increase fact row count | Verify lookup key uniqueness and join columns |
| Data types | Keys match on both sides; dates and decimals use intended types | Fix in the query steps, not by relying on automatic model detection |
| Soft-delete handling | Delete dates are retained when available | Decide deletion inclusion in measures/report definitions |
| Sensitive columns | No secrets or unnecessary PII in curated outputs | Remove them using Choose Columns before load |

A few source relationships intentionally require extra attention. `followers.following_id` is semantically expected to point to a profile, but the schema doesn't explicitly declare it as a foreign key. Validate it against `DimProfile`. The `profiles.user_id` and `users.profile_id` links run in opposite directions in the source schema; keep the dimensions separate until actual cardinality and matching behavior are verified.

### Final readiness checklist

- [ ] Every dimension has a written grain and a unique key.
- [ ] Every fact/bridge has a written grain and preserves the correct event rows.
- [ ] No fact tables have been merged together to make one wide table.
- [ ] All relationship keys use compatible types; ODBC identifiers are no longer Binary.
- [ ] All non-null foreign keys have been checked against the right key domain.
- [ ] Nulls and soft deletes are deliberately handled rather than silently removed.
- [ ] Large text, JSON payloads, credentials and unnecessary PII are excluded from curated outputs.
- [ ] QA checks pass before enabling load for curated queries.
- [ ] Staging queries remain available for lineage and troubleshooting, with load disabled where appropriate.

## Official Power Query and model-design references

- [Power Query best practices](https://learn.microsoft.com/power-query/best-practices)
- [Query folding guidance in Power BI Desktop](https://learn.microsoft.com/power-bi/guidance/power-query-folding)
- [Referencing queries](https://learn.microsoft.com/power-bi/guidance/power-query-referenced-queries)
- [Understand star schema and its importance for Power BI](https://learn.microsoft.com/power-bi/guidance/star-schema)
- [Create and manage relationships in Power BI Desktop](https://learn.microsoft.com/power-bi/desktop-create-and-manage-relationships)
