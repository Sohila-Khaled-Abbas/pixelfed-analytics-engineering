# PixelFed Analytics Engineering Documentation Hub

Welcome to the comprehensive engineering documentation for the PixelFed Analytics Engineering Lakehouse & Semantic Modeling project. This documentation suite covers the complete lifecycle from relational source contracts to mixed-format lakehouse ingestion, dimensional modeling, and semantic layer publishing.

---

## Documentation Taxonomy

```text
docs/
├── architecture/
│   ├── system-architecture.md         # End-to-end Medallion architecture & principles
│   ├── identity-consistency.md        # Deterministic IDs, foreign keys, & referential integrity rules
│   ├── project-roadmap.md             # Multi-phase engineering roadmap & delivery milestones
│   └── domain-realism-architecture.md  # Domain enrichment, business rules, and quality flow
├── contracts/
│   ├── data-dictionary.md             # Comprehensive 54-table column-level data dictionary
│   └── format-catalog.md              # Ingestion contract & 54-table format allocation matrix
├── ingestion/
│   ├── mixed-format-lakehouse.md      # Multi-format ingestion strategies & compression handling
│   ├── power-query-pipeline.md        # Full Power Query M ETL transformation pipeline (54 tables)
│   ├── power-query-ui-walkthrough.md  # Step-by-step visual ingestion guide in Power BI Desktop
│   ├── sqlite-odbc-staging.md         # Relational SQLite ODBC driver connection & M scripts
│   └── landing-data-refresh-runbook.md # Safe candidate generation, validation, and promotion
├── modeling/
│   ├── dimensional-galaxy-guide.md    # Kimball Galaxy Schema design, grain definitions, & Bus Matrix
│   ├── data-cleaning-playbook.md      # Null handling, type coercion, and deduplication playbook
│   ├── semantic-model-design.md       # Star schema relationships, cardinalities, & filter propagation
│   └── business-domain-data-contracts.md # Business grains, facts, and KPI definitions
└── semantic-layer/
    └── tmdl-semantic-models.md        # Tabular Model Definition Language (TMDL) & semantic staging
```

---

## Architecture & System Design

- **[System Architecture](architecture/system-architecture.md)**  
  Detailed architecture blueprint detailing the transition from the canonical 54-table MySQL source contract (`schema.md`) through the multi-format lakehouse landing layer into a Kimball star/galaxy semantic model.
- **[Identity Consistency Specification](architecture/identity-consistency.md)**  
  Standards for maintaining referential integrity across synthetic data generations, including entity graph traversal, temporal consistency (`as_of` boundaries), and surrogate key derivation.
- **[Project Roadmap](architecture/project-roadmap.md)**  
  Milestones, deliverables, and engineering roadmap covering Landing Ingestion, Staging Transformations, Dimensional Modeling, Semantic Layer, and Power BI report delivery.

---

## Data Contracts & Catalog

- **[Data Dictionary](contracts/data-dictionary.md)**  
  Exhaustive technical catalog documenting all 54 tables, 555 columns, MySQL operational data types, target Power Query/BI types, nullability rules, primary keys, and foreign key constraints.
- **[Format Catalog](contracts/format-catalog.md)**  
  Physical allocation contract assigning each table to exactly one native format (`csv_gz`, `csv`, `jsonl`, `json`, `xlsx`, `sqlite`) without synthetic format duplication.

---

## Ingestion & Pipeline Engineering

- **[Mixed-Format Lakehouse Ingestion](ingestion/mixed-format-lakehouse.md)**  
  Technical patterns for ingesting diverse raw file formats in Power Query, handling GZIP stream decompression, JSON array flattening, and newline-delimited JSON parsing.
- **[Power Query Pipeline Guide](ingestion/power-query-pipeline.md)**  
  Production-ready Power Query M scripts for all 54 tables, structured into modular staging queries (`stg_*`) with parameter-driven base paths.
- **[Power Query UI Walkthrough](ingestion/power-query-ui-walkthrough.md)**  
  Visual guide for manually loading each format into Power BI Desktop, verifying data types, headers, and encoding settings.
- **[SQLite ODBC Staging Guide](ingestion/sqlite-odbc-staging.md)**  
  Configuration and Power Query M patterns for connecting to the 13 SQLite operational tables via the SQLite3 ODBC driver.

---

## Dimensional Modeling & Cleansing

- **[Dimensional Galaxy Model Guide](modeling/dimensional-galaxy-guide.md)**  
  Architectural blueprint for the Gold Layer Galaxy Schema: shared conformed dimensions (`dim_users`, `dim_profiles`, `dim_date`, `dim_instances`) and grain-isolated fact tables (`fct_posts`, `fct_likes`, `fct_comments`, `fct_follows`, `fct_media`).
- **[Data Cleaning & Nulls Playbook](modeling/data-cleaning-playbook.md)**  
  Operational playbook detailing strategies for null imputation, categorical standardization, string trimming, and edge-case handling across operational entities.
- **[Semantic Model Design](modeling/semantic-model-design.md)**  
  Relationship topologies, cross-filter direction best practices, single-direction filter propagation, and ambiguity prevention in complex social graphs.

---

## Power BI Engineering End-to-End

- **[Power BI Engineering Playbook](power-bi-engineering-playbook.md)**  
  End-to-end GUI-first instructions for the existing `data/landing` datasets, Power Query transformations and M examples, QA queries, dynamic `DimDate`/`DimTime`, galaxy modeling, DAX measures, report UX, performance, security, and release checks. Read this before changing the semantic model.

---

## Semantic Layer & TMDL

- **[TMDL Semantic Models Guide](semantic-layer/tmdl-semantic-models.md)**  
  Automation guide for managing Microsoft Fabric / Power BI Tabular Model Definition Language (TMDL) scripts to deploy staging tables and semantic models as version-controlled code.


## Business-domain data and safe refresh

- **[Business-Domain Enrichment Architecture](architecture/domain-realism-architecture.md)** explains the enrichment pipeline, semantic quality gates, code ownership, and synthetic-data limitations.
- **[Business-Domain Data Contracts](modeling/business-domain-data-contracts.md)** defines table grains, the analytics bus matrix, independent fact grains, and KPI definitions.
- **[Landing Data Refresh Runbook](ingestion/landing-data-refresh-runbook.md)** gives PowerShell commands to smoke-test and generate into a candidate directory, validate quality, preserve the current landing zone, and refresh Power BI safely.
