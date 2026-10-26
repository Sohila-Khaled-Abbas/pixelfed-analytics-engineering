# Synthetic Workloads & Data Contracts

## Why there are two generators

The repository separates two different learning objectives:

1. src/generate_landing.py emits a schema-faithful, 54-table PixelFed-inspired relational source replica in mixed physical formats for Power Query, SQLite, and local Power BI modelling. The default row counts are deliberately modest for a local workstation.
2. src/generate_activity_stream.py emits a high-volume event fact dataset incrementally in monthly gzip-compressed JSON Lines partitions, plus a joinable dim_profile.csv.gz dimension. Actor and target profiles only appear after their synthetic account creation timestamp. It is designed for partition-aware ingestion and event analytics, not for emulating a live PixelFed deployment or distributed compute benchmark.

Every record is synthetic and deterministic for a fixed seed, event date range, and run arguments. All generated domains use reserved example.test hosts or generated IDs. Do not treat these datasets as sourced from PixelFed production, and do not use any generated auth-like fields as credentials.

## Relational domain realism

Before the source-replica generator validates and exports tables, src/domain_realism.py applies a product-domain layer:

- Local user/profile pairs and remote/federated profiles are kept distinct.
- Creator activity is skewed: a small creator cohort receives more posts and engagement than the median creator.
- Post creation uses an account-age-aware timeline and a realistic photo/video/text mix.
- Captions, hashtags, country/city fields, media types and visibility values have semantic meaning instead of generic table_column_000123 filler.
- Likes, comments, replies, reblogs, follows, and story views reference existing entities. Engagement is timestamped after its target post, and story views occur inside the referenced story's lifetime.
- Denormalized post counts (likes_count, reply_count, reblogs_count) and profile counts are recomputed from their underlying records.
- Product-specific assertions supplement schema/foreign-key checks, so invalid chronology and unreconciled metrics fail generation before export.

The synthetic content is designed to produce realistic analytics patterns, not to reproduce real user identities or exact PixelFed behavior. Distribution parameters are illustrative and should be treated as explicit modeling assumptions.

## Event stream grain and schema

src/generate_activity_stream.py writes one row per event:

| Field | Meaning |
| --- | --- |
| run_id | Reproducible identifier derived from the seed, date range, population, and event count |
| event_id | Stable key prefixed by run_id, unique across distinct generated configurations and repeatable for identical arguments |
| event_timestamp | When the product event occurred (event time) |
| event_date, event_hour | Derived event-time fields for partition and time-series analysis |
| event_type | One of the product actions such as post_created, post_viewed, like_created, comment_created, follow_created, or story_viewed |
| actor_profile_id | Synthetic profile that performed the event |
| target_profile_id | Optional profile targeted by a follow/report action |
| object_type, object_id | The post, story, profile, or hashtag referenced by the event |
| visibility | Visibility inherited from a referenced post when applicable |
| source_app | Client/worker channel (web, iOS, Android, API, or federation worker) |
| session_id, request_id | Synthetic trace dimensions for session and request analysis |
| ingested_at | Event ingestion timestamp, capped at the run's as-of time |
| is_late_arrival | Indicates a simulated ingest delay of at least 15 minutes |
| schema_version | Versioned event contract |
| properties | Type-specific, semi-structured product telemetry |

### Commands

A lightweight smoke test:

~~~powershell
python src/generate_activity_stream.py --events 10000 --profiles 2000 --start-date 2026-01-01 --as-of 2026-03-18T12:00:00Z --seed 42 --output-dir ./tmp_activity_stream
~~~

A larger exercise:

~~~powershell
python src/generate_activity_stream.py --events 1000000 --profiles 50000 --start-date 2024-01-01 --as-of 2026-10-26T12:00:00Z --seed 42 --output-dir ./data/activity_stream
~~~

The output includes manifest.json, quality_report.json, dimensions/dim_profile.csv.gz, and directories such as event_month=2026-03/events.jsonl.gz. The profile dimension contains country/language, local-versus-federated instance, privacy, creator tier, follower band, interest, and account creation time. High-activity creator IDs are aligned with the power_creator tier. The event generator buffers timestamps for one month and maintains the post/story reference state required for plausible event targets; it does not accumulate every event row in a single Python list. Memory use still grows with reference state, and this implementation is not a distributed processing engine.

## Analytics engineering exercises enabled

The stream can be ingested as a Bronze append-only event table and conformed in Silver. Good downstream exercises include:

- Deduplicate on event_id and compare event_timestamp with ingested_at; identical reruns are idempotent, while differing generator arguments receive a different run_id.
- Build a date partition filter and incremental load watermark.
- Use explicit grains for posts, views, likes, comments, follows, reports, and media processing.
- Reconcile generated relational metrics against event counts where their business definitions align.
- Track daily active profiles, post view-to-like rate, comment rate, creator cohorts, source-app mix, federation share, and late-arrival rate.
- Join events to dim_profile on actor_profile_id, use profile creation timestamps to assert activity chronology, and compare metrics by creator tier, country, language, privacy, or federation status.
- Flatten properties into typed downstream columns while retaining the raw JSON for schema evolution.
- Build a Gold star/galaxy model with conformed date, time, profile, post, source application, and event-type dimensions.

Avoid joining event facts together before aggregating to compatible grains; doing so can multiply counts. A view fact joined directly to likes and comments by post ID will generally fan out.

## Quality contracts

The stream manifest records the requested and written event counts, monthly row counts, event-type distributions, compressed bytes, distinct observed actors, late-arrival counts/rates, and explicit synthetic-data notes. The smoke tests assert exact row count, unique event IDs, no event after the as-of timestamp, partition existence, and existing post/story references.

The source-replica validator also retains schema shape, format allocation, row-count, primary/unique-key, foreign-key, and SQLite integrity checks. These contracts are complementary: a schema-perfect dataset can still be semantically unrealistic, so both classes of checks matter.

## What this is — and is not

**This is:** a practical analytics-engineering portfolio environment with reproducible synthetic source entities, plausible behavioral skew, domain quality rules, a partitioned event stream, mixed-format ingestion, dimensional modelling, and Power BI consumption.

**This is not:** actual PixelFed production data, a complete emulator of the PixelFed application, a guarantee of real-world distribution parameters, or proof of production-grade throughput. For real deployment benchmarking, use a dedicated workload generator, measured target infrastructure, and documented workload assumptions.
