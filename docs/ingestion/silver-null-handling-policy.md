# Silver Null-Handling Policy

## Purpose

The landing zone is Bronze: preserve source values and record defects. Silver is where normalization and explicit null policy belong. All records in this repository are synthetic.

A null is not one universal state:

- **Unknown / not supplied:** an optional profile bio, website, or disclosed location may be absent.
- **Not applicable:** a federated profile may have no local user row. Some media-processing columns may not apply to images.
- **No event recorded:** no email-verification or read timestamp has been recorded.
- **Absent optional relationship:** a post may have no place tag; this does not mean its author's profile location is missing.
- **Current lifecycle state:** a null deletion timestamp usually means no deletion timestamp is recorded; it should not be filled with today's date.

Never replace every null with zero, false, "Unknown", or the current timestamp. Do not infer a user's location from network identifiers. Preserve raw values so transformations remain auditable.

## Recommended policy by field family

| Field / pattern | Possible meaning | Silver treatment |
|---|---|---|
| profiles.bio, profiles.website, profiles.location | Optional, potentially undisclosed | Keep null; trim text; use "Not provided" only in a display label if needed |
| profiles.user_id, users.profile_id | Federated/non-local identity or missing pairing | Keep null when valid for the domain; use anti-joins to identify actual orphans |
| users.email_verified_at | No verification timestamp recorded | Preserve null; derive a separate status only if documented |
| contacts.response | No response sent yet when responded_at is null and the response is blank | Keep blank in raw data; normalize blank to null in a clean Silver column and report the count |
| statuses.place_id | Post is not explicitly geotagged | Keep null; do not borrow profile location |
| notifications.read_at, direct_messages.read_at | No read time recorded | Keep null; derive a read indicator only where source semantics support it |
| deleted_at | No deletion timestamp recorded | Keep null; derive a separate deletion flag if needed |
| Media thumbnail, HLS, processing fields | Depends on media family and pipeline state | Evaluate conditional applicability; do not impute video fields to images |
| Caption/comment/bio with whitespace | Formatting noise or empty text | Trim; convert trimmed empty strings to null; retain raw values |
| created_at with multiple formats | Same type represented inconsistently | Create a clean typed timestamp and parse-status flag; never invent dates |

## Power Query M patterns

### 1. Trim optional text without destroying nulls

Apply this only to text columns:

\`\`\`powerquery
CleanOptionalText = (value as nullable text) as nullable text =>
    if value = null then
        null
    else
        let
            trimmed = Text.Trim(value)
        in
            if trimmed = "" then null else trimmed
\`\`\`

Use the function in a staging query while preserving the raw field:

\`\`\`powerquery
let
    Source = Raw_Profiles,
    WithRawBio = Table.DuplicateColumn(Source, "bio", "bio_raw"),
    CleanedBio = Table.TransformColumns(
        WithRawBio,
        {{"bio", each CleanOptionalText(_), type nullable text}}
    )
in
    CleanedBio
\`\`\`

The clean bio is for downstream analysis; bio_raw is evidence for troubleshooting. Apply the same pattern to website and location after confirming the columns are text.

### 2. Normalize mixed timestamp strings

Create a new column instead of overwriting Bronze:

\`\`\`powerquery
ParseSourceDateTime = (value as any) as nullable datetime =>
    if value = null then
        null
    else
        let
            raw = Text.Trim(Text.From(value)),
            isoParsed = try DateTime.FromText(raw, [Culture = "en-US"]) otherwise null,
            slashParsed =
                if isoParsed <> null then
                    isoParsed
                else
                    try DateTime.FromText(
                        raw,
                        [Format = "yyyy/MM/dd HH:mm:ss", Culture = "en-US"]
                    ) otherwise null
        in
            slashParsed
\`\`\`

Add created_at_clean and created_at_parse_failed to Silver. A null source timestamp and a malformed non-null timestamp are different cases; track both.

\`\`\`powerquery
let
    Source = Raw_Statuses,
    WithRawCreatedAt = Table.DuplicateColumn(Source, "created_at", "created_at_raw"),
    WithCleanCreatedAt = Table.AddColumn(
        WithRawCreatedAt,
        "created_at_clean",
        each ParseSourceDateTime([created_at_raw]),
        type nullable datetime
    ),
    WithParseFlag = Table.AddColumn(
        WithCleanCreatedAt,
        "created_at_parse_failed",
        each [created_at_raw] <> null and [created_at_clean] = null,
        type logical
    )
in
    WithParseFlag
\`\`\`

Confirm the source connector returns created_at as text for this mixed-format export. If it already returns datetime values, adapt the function instead of converting through text unnecessarily.

## Generated nulls are not all the same

The generator uses field-aware natural missingness rates rather than scattering the same default 6% NULL probability across almost every nullable field. Examples include undisclosed profile metadata, optional post geotags, email-verification timestamps, unread notifications, unread direct messages, deletion lifecycle timestamps, and media alternative text. These rates are documented modelling assumptions, not estimates measured from PixelFed production data.

The generator records a pre-raw-quality profile for **every table and source-contract column** in `metadata/data_quality_report.json` under `field_missingness_before_raw_quality`. Each entry includes row count, NULL count/rate, blank-string count/rate, schema nullability, and whether the column is a primary key. It is calculated before the optional raw-quality defects are added, so the later Bronze issues can be distinguished from normal optional fields.

Use those counts as a starting point for profiling, not as automatic proof that a NULL is valid. In Silver, compare the field with its business meaning, schema constraints, row type, and relationships. A field can be nullable in the MySQL schema while still being practically required for a particular record subtype.

## Profile first, clean second

For every source table, profile: row count; per-column null counts and rates; primary-key nulls and duplicates; foreign-key anti-join counts; before/after blanks; timestamp parse failures and date ranges; number of rows changed or quarantined.

Separate **expected nulls** from **unexpected quality failures**. A null primary key is a contract failure. An undisclosed bio usually is not. Treat a missing foreign key as an orphan only if the relationship is required and the source domain says a local parent must exist.

## Suggested Silver acceptance gates

1. Primary keys have no nulls or duplicates.
2. Required relationships have zero unexplained orphans, including the local-versus-federated profile rule.
3. Optional text is trimmed; blank strings become null; null rates are reported, not automatically rejected.
4. Timestamp parse success rate is reported; future dates and negative event lags are checked against business rules.
5. Unknown numeric measures remain null. Use zero only where "no event" really means a measured zero.
6. Row counts and event-grain metrics are reconciled against the source manifest after refresh.

See docs/ingestion/raw-landing-to-silver-workflow.md for the Bronze → Silver → Gold workflow.
