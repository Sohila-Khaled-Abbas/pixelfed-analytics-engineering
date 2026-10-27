# Raw Landing → Silver Workflow

## Purpose

The project deliberately separates **business coherence** from **raw-source cleanliness**.

- **Business coherence:** account/profile identities, foreign keys, post/engagement relationships, media types, and event chronology are generated consistently.
- **Raw landing quality:** a small, reproducible set of source-style issues is injected after core domain validation so you can practice cleaning in Power Query instead of receiving already-clean Gold data.
- **Silver/staging:** transformations standardize values and types, apply null policy, identify duplicates, and report rejected rows without silently rewriting the raw source.

All records are synthetic. The raw quality profile is for learning, not a claim about real PixelFed production data.

## What issues are intentionally present?

The optional `src/raw_quality.py` module injects a deterministic, limited set of defects:

| Issue | Example | Recommended Silver treatment |
|---|---|---|
| Missing optional text | Optional bios, captions, replies, or descriptions may be null | Keep null when genuinely unknown; do not invent business meaning |
| Leading/trailing whitespace | Captions, bios, or replies padded with spaces | Trim text in Power Query; preserve raw columns if auditability matters |
| Mixed timestamp formats | Some `statuses.created_at` values use `yyyy/MM/dd HH:mm:ss` while others use ISO text | Parse with an explicit format/locale fallback; record conversion failures |
| Referential integrity | **Not deliberately broken** | Use anti-joins/key checks to detect accidental generator regressions |

The issue report is written to `data/landing/metadata/data_quality_report.json` under `raw_quality`. It distinguishes expected Bronze defects from generator contract failures. Generator `passed` describes schema/domain validation before issue injection; physical validation confirms file layout, headers, and row counts. Therefore, `passed=true` does not mean the raw landing data is clean.

## Safe refresh: keep current data until you approve a candidate

Run these commands in PowerShell from the repository root:

```powershell
Set-Location "D:\courses\Data Analysis 26-27\Projects\PixelFed"
git status --short --branch
python -m pip install -r requirements.txt
```

First generate a small candidate. **This does not replace `data/landing`** because promotion is opt-in:

```powershell
python src/refresh_landing.py --scale 0.03 --seed 42 --as-of 2026-10-27T12:00:00Z
```

Inspect the candidate path printed by the script and review its manifest and quality report. Validate it independently if needed:

```powershell
python src/validate_landing.py --landing "data\landing_candidate_YYYYMMDD_HHMMSS"
Get-Content "data\landing_candidate_YYYYMMDD_HHMMSS\metadata\data_quality_report.json" -Raw
```

Replace the placeholder with the actual candidate folder name. If you approve the full-scale data, run:

```powershell
python src/refresh_landing.py --scale 1.0 --seed 42 --as-of 2026-10-27T12:00:00Z --promote
```

Each successful promoted run renames the previous `data/landing` to a timestamped sibling such as `data/landing_backup_20261027_143000`. The script retains backups and only promotes a candidate after generation, raw-quality-report checks, and physical validation pass. Keep enough free disk space for a candidate plus the backup. Do not delete backups until Power BI refresh and reconciliation succeed.

For a small sample that is explicitly intended to become the active landing data, add `--promote` to the small-scale command. Otherwise, it stays a candidate.

## Recommended project process

1. **Source contract:** read `schema.md`, the architecture diagram, and `docs/modeling/business-domain-data-contracts.md`.
2. **Landing/Bronze:** inspect `metadata/manifest.json`, `row_counts.csv`, `schema_contract.json`, and `data_quality_report.json`. Never edit raw tables manually as the permanent fix.
3. **Profiling:** measure null rates, duplicate business events, distinct counts, min/max dates, and key coverage in Power Query or Python.
4. **Staging/Silver:** create one staging query per source table. Keep raw queries connection-only when practical; reference them from typed/cleaned staging queries.
5. **Clean consistently:** trim free text, normalize timestamp formats, set explicit data types/locales, preserve genuine nulls, and add quality flags rather than silently dropping records.
6. **Conform dimensions:** maintain stable `DimProfile` identity, create `DimDate` and `DimTime` from normalized timestamps, and define one-to-many single-direction relationships where the business grain supports them.
7. **Build facts at explicit grain:** for example one row per post, like event, comment event, follow edge, media asset, or story view. Do not join multiple event facts together before aggregation; that multiplies measures.
8. **Validate Silver/Gold:** test primary/foreign keys, duplicate business keys, null policies, event chronology, row-count reconciliation, and metric definitions.
9. **Publish reproducibly:** commit generator, tests, contracts, and Markdown guides. `data/landing` and backups remain ignored/local because they are generated and may be large.

## Suggested quality checks

- Row count by table and source file against the manifest.
- Distinct primary keys and null primary keys.
- Orphan counts with anti-joins for every declared relationship.
- `Text.Trim` effects and before/after null rates.
- Timestamp parse success rate, earliest/latest event time, and future-dated records.
- Duplicate candidate keys at the event grain, distinguished from repeated IDs.
- Reconciliation of post counters to active likes, replies, and boosts after Silver rules are applied.
- Reconcile daily metrics before and after the landing refresh; document expected changes caused by a new seed or as-of cutoff.

## Rollback

If refresh or Power BI reconciliation fails, close Power BI Desktop and rename the new `data/landing` to a diagnostic candidate path. Rename the timestamped backup back to `data/landing`. Never delete the backup as the first rollback step.
