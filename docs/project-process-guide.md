# PixelFed Analytics Engineering: End-to-End Project Guide

## Business questions

Use the project to analyze publishing, engagement, creator cohorts, photo/video/text mix, local versus federated activity, moderation workload, and event timing.

## Repository map

| Path | Responsibility |
|---|---|
| `schema.md` | 54-table source contract |
| `src/schema_generator_core.py` | Schema-driven generation and core validation |
| `src/domain_realism.py` | Product patterns and event relationships |
| `src/business_enrichment.py` | Topic profiles, settings, media, notifications, moderation |
| `src/raw_quality.py` | Intentional raw-source defects for cleaning exercises |
| `src/generate_landing.py` | Mixed native-format export and metadata |
| `src/refresh_landing.py` | Candidate generation, validation, backup and optional promotion |
| `src/validate_landing.py` | Physical files, schema, row counts and SQLite checks |
| `docs/` | Architecture, ingestion, modeling and process guides |
| `powerbi/` | Semantic model and report assets |

## Bronze, Silver, Gold

### Bronze / landing

Each source table remains in its assigned native format: compressed CSV, CSV, JSONL, JSON, XLSX, or SQLite. Treat landing as an immutable source snapshot. The core generator preserves canonical account/profile identity, valid foreign keys, meaningful event relationships and event chronology. The optional raw-quality layer adds a small, reported set of source-style defects after those checks.

### Silver / staging

Use Power Query to reference raw queries and create typed staging queries. Trim text, normalize timestamps with explicit formats/locales, apply a documented null policy, test keys with anti-joins, and profile duplicate business events using a declared grain. Add audit fields such as `Source_Table`, `Is_Valid`, and `Quality_Issue`. Keep rejected records available for review rather than silently deleting them.

### Gold / analytics model

Build a galaxy model with conformed dimensions such as `DimDate`, `DimTime`, `DimProfile`, `DimUser`, and `DimInstance`. Keep fact grain explicit: `FctPosts` one row per post, `FctLikes` one row per like event, `FctComments` one row per comment, `FctFollows` one row per directed follow edge, and `FctMedia` one row per media asset. Do not join multiple many-side facts together before aggregation because that multiplies measures.

## Safe refresh process

Start with a candidate that does not replace the active landing folder:

```powershell
python src/refresh_landing.py --scale 0.03 --seed 42 --as-of 2026-10-27T12:00:00Z
```

Review the candidate folder path printed by the script, then inspect `metadata/manifest.json` and `metadata/data_quality_report.json`. After reviewing and approving the full-size candidate, explicitly promote it:

```powershell
python src/refresh_landing.py --scale 1.0 --seed 42 --as-of 2026-10-27T12:00:00Z --promote
```

Promotion keeps the previous `data/landing` as a timestamped backup. Keep that backup until Power BI refresh and metric reconciliation succeed. Generated landing data and backups remain Git-ignored and local.

## Quality gates

1. Core schema/domain/business checks pass before raw defects are injected.
2. Raw issue counts are recorded under `raw_quality` in the quality report.
3. Physical validation passes and every source table has one assigned representation.
4. Primary keys and foreign keys remain intact; no intentional orphan relationships are injected.
5. Power Query handles whitespace, missing optional text and mixed timestamp formats.
6. Silver/Gold row counts, date ranges, daily engagement metrics and fact-grain measures reconcile.
7. Commit code, tests, contracts, diagrams and guides—not generated data files.

## Suggested portfolio walkthrough

1. Explain the schema and architecture.
2. Generate a candidate and inspect the manifest/report.
3. Profile the raw data and demonstrate three cleaning cases.
4. Build staging queries and conformed date/time/profile dimensions.
5. Build facts one at a time and test relationships and grain.
6. Add DAX only after reconciliation.
7. Document the refresh, quality decisions and material metric changes.
