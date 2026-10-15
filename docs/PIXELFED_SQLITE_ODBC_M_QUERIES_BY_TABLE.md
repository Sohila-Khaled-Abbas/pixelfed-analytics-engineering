# PixelFed SQLite ODBC: table-by-table Power Query M guide

This guide fixes the affected SQLite ODBC queries by explicitly casting driver-sensitive numeric fields to SQLite `TEXT` in the SQL projection, then converting the returned text to the correct Power Query type. Create one blank query for each table and paste that table's complete M expression into **Home → Transform data → New Source → Blank Query → Advanced Editor**.

**Required DSN:** `PixelFedSQLite` (64-bit ODBC User DSN). Point it to:

`D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing\sqlite\pixelfed_operational_tables.sqlite`

**Why two stages?** `Odbc.Query` executes the SQL statement and returns its results as a Power Query table; `Table.TransformColumnTypes` then applies explicit Power Query types. See Microsoft's documentation for [Odbc.Query](https://learn.microsoft.com/en-us/powerquery-m/odbc-query) and [Table.TransformColumnTypes](https://learn.microsoft.com/en-us/powerquery-m/table-transformcolumntypes).

## Important typing rules

- Numeric primary/foreign keys and integer flags in this guide use `Int64.Type` after the SQL cast. Convert validated 0/1 flags to `type logical` later in the curated layer if that is useful for reporting.
- String identifiers stay text: OAuth `id`, `access_token_id`, session `id`, emails, keys, tokens, `filterable_type`, and `filter_type` are not numeric fields.
- `user_filters.filterable_id` is numeric in the supplied schema, but it is polymorphic: interpret it together with `filterable_type`; do not relate it directly to one dimension unless the type indicates that entity.
- `sessions.last_activity` remains an integer because the schema defines it as an integer. Treat it as Unix epoch time only after confirming the actual source encoding and unit.
- `password_resets` contains no numeric ID. Its `email` and `token` are text, and `created_at` is a nullable datetime.
- This exact staging guide includes some credential-like columns for **synthetic schema practice**. In a real dataset, remove `user_token`, `random_token`, OAuth secrets/scopes, session payloads, invite keys/tokens, password-reset tokens, IP addresses and other sensitive values before loading the reporting semantic model. Better still, exclude them in the SQL projection so they never enter Power BI.

## How to apply each query

1. In Power Query Editor, create a Blank Query.
2. Rename it exactly as shown (for example, `stg_contacts`).
3. Open **Advanced Editor**, replace the editor content with the M query, and select **Done**.
4. Inspect the `Source` step first. The cast fields should be text values such as `"42"` rather than `Binary`.
5. Inspect the `Typed` step. The same fields should become Whole Number (`Int64.Type`) and timestamps should become Date/Time.
6. Confirm no conversion errors, compare row counts with the source table, then repeat for the next table.
7. Choose **Close & Apply** only after all the affected queries preview correctly.

If the SQL cast still displays Binary or yields malformed text, stop and inspect the source with the diagnostic steps at the end of this guide. Don't try to repair unknown byte sequences by blindly converting them to numbers.

---

## Contacts — `stg_contacts`

**Cast to text before Power Query typing:** id, user_id, response_requested

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                CAST(""response_requested"" AS TEXT) AS ""response_requested"",
                ""message"",
                ""response"",
                ""read_at"",
                ""responded_at"",
                ""created_at"",
                ""updated_at""
             FROM ""contacts"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"user_id", Int64.Type},
                {"response_requested", Int64.Type},
                {"message", type text},
                {"response", type text},
                {"read_at", type datetime},
                {"responded_at", type datetime},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## Email verifications — `stg_email_verifications`

**Cast to text before Power Query typing:** id, user_id

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                ""email"",
                ""user_token"",
                ""random_token"",
                ""created_at"",
                ""updated_at""
             FROM ""email_verifications"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"user_id", Int64.Type},
                {"email", type text},
                {"user_token", type text},
                {"random_token", type text},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## Follow requests — `stg_follow_requests`

**Cast to text before Power Query typing:** id, follower_id, following_id, is_rejected, is_local

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""follower_id"" AS TEXT) AS ""follower_id"",
                CAST(""following_id"" AS TEXT) AS ""following_id"",
                CAST(""is_rejected"" AS TEXT) AS ""is_rejected"",
                CAST(""is_local"" AS TEXT) AS ""is_local"",
                ""created_at"",
                ""updated_at""
             FROM ""follow_requests"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"follower_id", Int64.Type},
                {"following_id", Int64.Type},
                {"is_rejected", Int64.Type},
                {"is_local", Int64.Type},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## Newsroom — `stg_newsroom`

**Cast to text before Power Query typing:** id, user_id, force_modal, show_timeline, show_link, auth_only

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                ""header_photo_url"",
                ""title"",
                ""slug"",
                ""category"",
                ""summary"",
                ""body"",
                ""body_rendered"",
                ""link"",
                CAST(""force_modal"" AS TEXT) AS ""force_modal"",
                CAST(""show_timeline"" AS TEXT) AS ""show_timeline"",
                CAST(""show_link"" AS TEXT) AS ""show_link"",
                CAST(""auth_only"" AS TEXT) AS ""auth_only"",
                ""published_at"",
                ""created_at"",
                ""updated_at""
             FROM ""newsroom"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"user_id", Int64.Type},
                {"header_photo_url", type text},
                {"title", type text},
                {"slug", type text},
                {"category", type text},
                {"summary", type text},
                {"body", type text},
                {"body_rendered", type text},
                {"link", type text},
                {"force_modal", Int64.Type},
                {"show_timeline", Int64.Type},
                {"show_link", Int64.Type},
                {"auth_only", Int64.Type},
                {"published_at", type datetime},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## OAuth access tokens — `stg_oauth_access_tokens`

**Cast to text before Power Query typing:** user_id, client_id, revoked

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                CAST(""client_id"" AS TEXT) AS ""client_id"",
                ""name"",
                ""scopes"",
                CAST(""revoked"" AS TEXT) AS ""revoked"",
                ""created_at"",
                ""updated_at"",
                ""expires_at""
             FROM ""oauth_access_tokens"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", type text},
                {"user_id", Int64.Type},
                {"client_id", Int64.Type},
                {"name", type text},
                {"scopes", type text},
                {"revoked", Int64.Type},
                {"created_at", type datetime},
                {"updated_at", type datetime},
                {"expires_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## OAuth authorization codes — `stg_oauth_auth_codes`

**Cast to text before Power Query typing:** user_id, client_id, revoked

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                CAST(""client_id"" AS TEXT) AS ""client_id"",
                ""scopes"",
                CAST(""revoked"" AS TEXT) AS ""revoked"",
                ""expires_at""
             FROM ""oauth_auth_codes"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", type text},
                {"user_id", Int64.Type},
                {"client_id", Int64.Type},
                {"scopes", type text},
                {"revoked", Int64.Type},
                {"expires_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## OAuth clients — `stg_oauth_clients`

**Cast to text before Power Query typing:** id, user_id, personal_access_client, password_client, revoked

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                ""name"",
                ""secret"",
                ""redirect"",
                CAST(""personal_access_client"" AS TEXT) AS ""personal_access_client"",
                CAST(""password_client"" AS TEXT) AS ""password_client"",
                CAST(""revoked"" AS TEXT) AS ""revoked"",
                ""created_at"",
                ""updated_at""
             FROM ""oauth_clients"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"user_id", Int64.Type},
                {"name", type text},
                {"secret", type text},
                {"redirect", type text},
                {"personal_access_client", Int64.Type},
                {"password_client", Int64.Type},
                {"revoked", Int64.Type},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## OAuth refresh tokens — `stg_oauth_refresh_tokens`

**Cast to text before Power Query typing:** revoked

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                ""id"",
                ""access_token_id"",
                CAST(""revoked"" AS TEXT) AS ""revoked"",
                ""expires_at""
             FROM ""oauth_refresh_tokens"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", type text},
                {"access_token_id", type text},
                {"revoked", Int64.Type},
                {"expires_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## Pages — `stg_pages`

**Cast to text before Power Query typing:** id, category_id, active, cached

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                ""root"",
                ""slug"",
                ""title"",
                CAST(""category_id"" AS TEXT) AS ""category_id"",
                ""content"",
                ""template"",
                CAST(""active"" AS TEXT) AS ""active"",
                CAST(""cached"" AS TEXT) AS ""cached"",
                ""active_until"",
                ""created_at"",
                ""updated_at""
             FROM ""pages"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"root", type text},
                {"slug", type text},
                {"title", type text},
                {"category_id", Int64.Type},
                {"content", type text},
                {"template", type text},
                {"active", Int64.Type},
                {"cached", Int64.Type},
                {"active_until", type datetime},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## Sessions — `stg_sessions`

**Cast to text before Power Query typing:** user_id, last_activity

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                ""ip_address"",
                ""user_agent"",
                ""payload"",
                CAST(""last_activity"" AS TEXT) AS ""last_activity""
             FROM ""sessions"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", type text},
                {"user_id", Int64.Type},
                {"ip_address", type text},
                {"user_agent", type text},
                {"payload", type text},
                {"last_activity", Int64.Type}
            },
            "en-US"
        )
in
    Typed
```

## User filters — `stg_user_filters`

**Cast to text before Power Query typing:** id, user_id, filterable_id

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                CAST(""filterable_id"" AS TEXT) AS ""filterable_id"",
                ""filterable_type"",
                ""filter_type"",
                ""created_at"",
                ""updated_at""
             FROM ""user_filters"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"user_id", Int64.Type},
                {"filterable_id", Int64.Type},
                {"filterable_type", type text},
                {"filter_type", type text},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## User invites — `stg_user_invites`

**Cast to text before Power Query typing:** id, user_id, profile_id

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                CAST(""id"" AS TEXT) AS ""id"",
                CAST(""user_id"" AS TEXT) AS ""user_id"",
                CAST(""profile_id"" AS TEXT) AS ""profile_id"",
                ""email"",
                ""message"",
                ""key"",
                ""token"",
                ""valid_until"",
                ""used_at"",
                ""created_at"",
                ""updated_at""
             FROM ""user_invites"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"id", Int64.Type},
                {"user_id", Int64.Type},
                {"profile_id", Int64.Type},
                {"email", type text},
                {"message", type text},
                {"key", type text},
                {"token", type text},
                {"valid_until", type datetime},
                {"used_at", type datetime},
                {"created_at", type datetime},
                {"updated_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## Password resets — `stg_password_resets`

**Cast to text before Power Query typing:** No numeric ID casts required; validate text and datetime fields.

```powerquery
let
    Source =
        Odbc.Query(
            "dsn=PixelFedSQLite",
            "SELECT
                ""email"",
                ""token"",
                ""created_at""
             FROM ""password_resets"""
        ),
    Typed =
        Table.TransformColumnTypes(
            Source,
            {
                {"email", type text},
                {"token", type text},
                {"created_at", type datetime}
            },
            "en-US"
        )
in
    Typed
```

## `password_resets`: additional security note

There is no numeric ID in this table, so do not add an `id` cast or invent an ID. The query above verifies text/date typing, but a production Power BI semantic model should not import the reset token. For an analytics-only query, remove `token` from the SQL projection and from the M type list; retain only `email` if genuinely needed (prefer a hashed/surrogate join key or aggregated metrics) and `created_at`.

## Diagnostic if an ODBC value still appears as Binary

Create a temporary **diagnostic query** for one failing field (for example, `contacts.id`) using `Odbc.Query` and compare these SQLite expressions in the SQL statement:

- `typeof("id")` — SQLite's stored value class (`integer`, `text`, `blob`, etc.).
- `quote("id")` — a readable representation where possible.
- `hex("id")` — the raw byte representation.
- `CAST("id" AS TEXT)` — SQLite's text conversion.
- `CAST("id" AS INTEGER)` — SQLite's numeric conversion.

Interpret the results before choosing a fix:

- If `typeof` is `integer` and `CAST(... AS TEXT)` returns digits, keep the query pattern in this guide.
- If `typeof` is `blob`, do not assume those bytes are a string representation of an integer. Inspect the data-generation/export step and correct the storage type or decoding logic there.
- If SQL returns clean digits but Power Query still reports `Binary`, test the DSN/driver with a fresh query and verify that the query is using `Odbc.Query` rather than relying on driver-inferred metadata from `Odbc.DataSource`.
- If the text-to-`Int64.Type` step errors, check for non-digit characters, empty strings, overflows, or unexpected null markers before applying a conversion.

## Validation checklist

- [ ] Each query name starts with `stg_` and matches its source table.
- [ ] SQL `CAST(... AS TEXT)` output is readable text for every field listed as cast-sensitive.
- [ ] Every numeric ID/flag casts to `Int64.Type` without errors.
- [ ] OAuth token IDs and session IDs stay `type text`.
- [ ] `password_resets` has no fabricated numeric ID.
- [ ] Timestamp columns are nullable Date/Time where defined nullable in the schema.
- [ ] `sessions.last_activity` remains an integer unless its epoch unit is confirmed.
- [ ] Sensitive columns are excluded from the curated semantic model.
- [ ] Loaded row counts match each source table and keys are checked for uniqueness.
