# Portfolio Roadmap

## Phase 1 — Schema contract and source simulation
- [x] Parse the supplied 54-table MySQL schema.
- [x] Generate deterministic synthetic records.
- [x] Assign each source table to one format only.
- [x] Produce a manifest, row counts, and a data-quality report.

## Phase 2 — Multi-format ingestion
- [x] Prepare Power Query templates for CSV, CSV.GZ, JSON, JSONL, XLSX, and SQLite.
- [ ] Paste the M queries into Power BI Desktop and validate row counts.
- [ ] Record any Power Query type coercion exceptions in the data-quality report.
- [ ] Confirm source key uniqueness and relationships after import.

## Phase 3 — Curated model
- [ ] Build `DimDate`, `DimProfile`, `DimStatus`, and `DimHashtag`.
- [ ] Build `FactPostMetrics`, `FactLikes`, `FactComments`, `FactMedia`, `FactFollows`, and `BridgeStatusHashtag` at explicit grains.
- [ ] Create role-playing dimensions for follower/followed and actor/recipient roles.
- [ ] Add a documented measures table and reusable DAX measures.

## Phase 4 — Report and operations
- [ ] Executive overview page.
- [ ] Content performance and engagement page.
- [ ] Data-quality and ingestion monitoring page.
- [ ] Save a Power BI Project (PBIP) with source-controlled report/model definitions.
- [ ] Add refresh instructions, screenshots, lineage, and a short demo to the README.

## Phase 5 — Optional extension
- [ ] Add Parquet and Arrow Feather as distinct assigned source formats once PyArrow is available; do not duplicate existing tables across formats.
- [ ] Add automated validation to a CI workflow.
- [ ] Add an incremental-load simulation and change-data-capture exercise.
