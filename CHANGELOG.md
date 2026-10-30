# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-18

### Added
- **Canonical Schema Contract**: 54-table, 555-column relational contract adapted from the [DrawSQL PixelFed Template](https://drawsql.app/templates/pixelfed).
- **Mixed-Format Landing Engine**: Synthetic generator producing deterministic lakehouse files across 6 physical storage engines (`csv_gz`: 11, `csv`: 10, `jsonl`: 8, `json`: 5, `xlsx`: 7, `sqlite`: 13).
- **Lakehouse Landing Zone Validation Suite**: Comprehensive schema contract, format assignment, row count, and SQLite referential integrity verification tool (`src/validate_landing.py`).
- **Kimball Galaxy Schema Models**: Gold Layer DDL definitions (`database/dimensional_models_ddl.sql`) and Power Query M transformations for conformed dimensions (`dim_users`, `dim_profiles`, `dim_date`, `dim_instances`, `dim_hashtags`) and grain-isolated fact tables (`fct_posts`, `fct_likes`, `fct_comments`, `fct_follows`, `fct_media`, `fct_story_views`).
- **Automated Testing Suite**: 13 unit, contract, determinism, and referential integrity tests in `tests/` executed via `pytest`.
- **Software Engineering Infrastructure**:
  - GitHub Actions CI/CD workflows (`.github/workflows/ci.yml`, `.github/workflows/documentation.yml`).
  - GitHub PR and Issue forms (`.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`).
  - Modern Python packaging & tool configuration (`pyproject.toml`, `requirements-dev.txt`, `.editorconfig`, `.pre-commit-config.yaml`).
- **Comprehensive Documentation Hub**: Modular docs taxonomy covering Architecture, Contracts, Ingestion, Dimensional Modeling, and Semantic Layer (`docs/README.md`).


## Unreleased — Egyptian engagement contracts

- Sample activity in Cairo civil time with versioned hourly assumptions and timezone data.
- Enforce actor registration and post/story lifecycle chronology; correct comment raw-quality targets.
- Revalidate keys and paired identities across native exports, including exact bigint handling.
- Add auditable Silver cleaning and a core engagement galaxy with eight fact tables, role keys and weighted tags.
- Record source/config/reference/dependency provenance; extend regression checks and CI galaxy smoke build.
- Document source assumptions, nulls, grains, relationship paths and protected-branch review workflow.
