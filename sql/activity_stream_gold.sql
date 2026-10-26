-- PixelFed-inspired synthetic event stream: Bronze -> Silver -> Gold.
-- Run from the repository root with DuckDB installed (pip install duckdb).
-- Expected input: data/activity_stream/event_month=YYYY-MM/events.jsonl.gz
-- All generated events are synthetic. Metrics are workload exercises, not production KPIs.

-- BRONZE: preserve the raw event shape and Hive-style month partition.
CREATE OR REPLACE VIEW bronze_activity_events AS
SELECT *
FROM read_json_auto(
    'data/activity_stream/event_month=*/events.jsonl.gz',
    format = 'newline_delimited',
    union_by_name = true,
    hive_partitioning = true
);

-- SILVER: cast the analytics contract, preserve run identity, and deduplicate repeat ingests.
-- object_id is deliberately normalized to VARCHAR because it can identify numeric post/story
-- IDs or string hashtag values depending on object_type.
CREATE OR REPLACE VIEW silver_activity_events AS
SELECT
    CAST(run_id AS VARCHAR) AS run_id,
    CAST(event_id AS VARCHAR) AS event_id,
    TRY_CAST(event_timestamp AS TIMESTAMPTZ) AS event_timestamp_utc,
    TRY_CAST(ingested_at AS TIMESTAMPTZ) AS ingested_at_utc,
    TRY_CAST(event_date AS DATE) AS event_date,
    TRY_CAST(event_hour AS TINYINT) AS event_hour,
    CAST(event_type AS VARCHAR) AS event_type,
    TRY_CAST(actor_profile_id AS BIGINT) AS actor_profile_id,
    TRY_CAST(target_profile_id AS BIGINT) AS target_profile_id,
    CAST(object_type AS VARCHAR) AS object_type,
    CAST(object_id AS VARCHAR) AS object_id,
    CAST(visibility AS VARCHAR) AS visibility,
    CAST(source_app AS VARCHAR) AS source_app,
    TRY_CAST(is_federated AS BOOLEAN) AS is_federated,
    CAST(session_id AS VARCHAR) AS session_id,
    CAST(request_id AS VARCHAR) AS request_id,
    TRY_CAST(is_late_arrival AS BOOLEAN) AS is_late_arrival,
    TRY_CAST(schema_version AS INTEGER) AS schema_version,
    properties
FROM bronze_activity_events
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY event_id
    ORDER BY ingested_at DESC NULLS LAST
) = 1;

-- GOLD: one row per event date. Do not join event types together before aggregation;
-- independent facts joined at post grain can multiply counts.
CREATE OR REPLACE VIEW gold_daily_product_metrics AS
SELECT
    event_date,
    COUNT(DISTINCT actor_profile_id) AS daily_active_profiles,
    COUNT(*) FILTER (WHERE event_type = 'post_created') AS posts_created,
    COUNT(*) FILTER (WHERE event_type = 'post_viewed') AS post_views,
    COUNT(*) FILTER (WHERE event_type = 'like_created') AS likes_created,
    COUNT(*) FILTER (WHERE event_type = 'comment_created') AS comments_created,
    COUNT(*) FILTER (WHERE event_type = 'follow_created') AS follows_created,
    COUNT(*) FILTER (WHERE event_type = 'story_created') AS stories_created,
    COUNT(*) FILTER (WHERE event_type = 'story_viewed') AS story_views,
    COUNT(*) FILTER (WHERE event_type = 'report_created') AS reports_created,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE event_type = 'like_created')
        / NULLIF(COUNT(*) FILTER (WHERE event_type = 'post_viewed'), 0),
        2
    ) AS likes_per_100_post_views,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_late_arrival)
        / NULLIF(COUNT(*), 0),
        2
    ) AS late_arrival_pct
FROM silver_activity_events
WHERE event_date IS NOT NULL
GROUP BY event_date;

-- GOLD: one row per event date and source application for channel/federation comparisons.
CREATE OR REPLACE VIEW gold_daily_source_app_metrics AS
SELECT
    event_date,
    source_app,
    COUNT(*) AS event_count,
    COUNT(DISTINCT actor_profile_id) AS active_profiles,
    COUNT(*) FILTER (WHERE is_federated) AS federated_events,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_federated)
        / NULLIF(COUNT(*), 0),
        2
    ) AS federated_event_pct
FROM silver_activity_events
WHERE event_date IS NOT NULL
GROUP BY event_date, source_app;
