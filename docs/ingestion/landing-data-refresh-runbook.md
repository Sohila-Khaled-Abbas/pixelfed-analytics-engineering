# Landing Data Refresh Runbook (Safe, Reproducible, Reviewable)

## Why use a candidate directory

The default destination is data/landing, a generated Git-ignored directory. A run there replaces generator-owned table files and metadata for the assigned formats. Protect the current landing data by generating into a separate candidate path, validating it, and comparing it first. Publish the generator, tests, contracts, guides, and diagrams—not the generated tables.

## 1. Inspect current state

Run from PowerShell:

```powershell
Set-Location "D:coursesData Analysis 26-27ProjectsPixelFed"

git status --short --branch
Get-ChildItem .data -Directory | Select-Object Name, LastWriteTime
if (Test-Path .datalandingmetadatamanifest.json) {
    Get-Content .datalandingmetadatamanifest.json -Raw
}
if (Test-Path .datalandingmetadatadata_quality_report.json) {
    Get-Content .datalandingmetadatadata_quality_report.json -Raw
}
```

Preserve the current manifest and row_counts.csv as the baseline. Do not regenerate into the active landing directory just to test changed code.

## 2. Run a small smoke generation

This only writes to a candidate folder:

```powershell
python -m pip install -r requirements.txt
python .srcgenerate_landing.py --scale 0.03 --seed 42 --as-of 2026-10-27T11:00:00Z --output-dir .datalanding_smoke
python .srcalidate_landing.py --landing .datalanding_smoke
```

Review data/landing_smoke/metadata/data_quality_report.json and confirm passed, domain_quality.passed, and business_quality.passed are true. The on-disk validator checks the exported file contract; generation-time checks validate behavioral semantics.

## 3. Generate a full candidate

After the smoke run succeeds, generate to a fresh path:

```powershell
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$candidate = ".datalanding_candidate_$stamp"
python .srcgenerate_landing.py --scale 1.0 --seed 42 --as-of 2026-10-27T11:00:00Z --output-dir $candidate
python .srcalidate_landing.py --landing $candidate
Get-Content "$candidatemetadatadata_quality_report.json" -Raw
Get-Content "$candidatemetadatamanifest.json" -Raw
```

Scale 1.0 is the default relational replica size, not a big-data benchmark. Use src/generate_activity_stream.py for separate partitioned scale-oriented event workloads.

## 4. Compare the candidate with existing data

Before promotion, verify:

- All 54 tables appear exactly once in the assigned physical formats.
- Manifest table list, row_counts.csv, actual row counts, and column counts agree.
- passed, domain_quality.passed, and business_quality.passed are true.
- Business-quality counts show zero media-type mismatches and zero comments/bookmarks/reports before the target post.
- Every synthetic device IP is in the documentation-only ranges.
- Local/federated profile mix, creator concentration, photo/video/text mix, visibility, topic labels, and engagement mix look plausible for the intended exercise.
- Power Query source paths still point at the correct landing root.

For row-count comparison, load both metadata/row_counts.csv files in Excel or Power Query and merge by table_name. Compare row_count, column_count, storage_format, and source_path. Fixed seed and scale make row counts stable; generated row values change when generation logic changes.

## 5. Back up before promotion

Only after the comparison passes, make a dated backup. Ensure there is enough free space:

```powershell
$backup = ".datalanding_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item .datalanding $backup -Recurse
if (-not (Test-Path "$backupmetadatamanifest.json")) {
    throw "Backup verification failed: existing manifest was not copied."
}
```

Promotion is a separate deliberate action. Close Power BI Desktop and any process reading the files. Keep the backup until refresh and metric reconciliation succeed. Do not recursively delete the active landing folder as a cleanup shortcut. If paths cross volumes or the current directory contains user-created files, prefer a verified manual copy rather than renaming directories.

## 6. Refresh Power BI

1. Open the PBIX/PBIP project and refresh against the candidate path.
2. Check Power Query errors, row counts, types, key nulls/duplicates, and anti-join orphan checks.
3. Compare daily posts, content types, active profiles, likes, comments, follows, media size, and moderation reports with the last report snapshot.
4. Check date/time dimensions, role-playing relationships, and DAX filter context.
5. Save a new report version before replacing the existing deliverable.

## 7. Publish code, not generated data

Files under data/landing, data/landing_*, and common generated file types are Git-ignored. Verify the change set:

```powershell
git status --short --ignored
git diff --check
git status --short
```

Do not force-add CSV, CSV.GZ, JSONL, XLSX, SQLite, report exports, or account/device-like records just to demonstrate that the generator ran.

## Troubleshooting

| Symptom | Action |
|---|---|
| business_quality.passed is false | Read business_quality.errors and fix the generator or fixture, not the report after export. |
| Row counts differ unexpectedly | Compare seed, scale, schema version, and metadata before treating the change as a defect. |
| SQLite foreign-key check fails | Inspect the violating table and fix its relationship at generation time. |
| Power BI cannot refresh | Confirm path parameter, connector, GZIP handling, sheet names, and SQLite ODBC configuration. |
| Disk space is constrained | Smoke-test with scale 0.03, use the larger data drive, and remove only verified temporary candidates—not the active landing zone. |
