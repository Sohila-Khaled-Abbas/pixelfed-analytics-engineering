# Architecture

```mermaid
flowchart TD
    A[MySQL schema.md contract] --> B[Schema-driven synthetic generator]
    B --> R[Domain realism and business enrichment]
    R --> C[Identity, schema and domain quality gates]
    C --> D1[CSV.GZ batch files]
    C --> D2[CSV tabular files]
    C --> D3[JSONL event streams]
    C --> D4[JSON document arrays]
    C --> D5[XLSX reference extracts]
    C --> D6[SQLite operational subset]
    D1 --> E[Power Query staging]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    D6 --> E
    E --> F[Curated star schema]
    F --> G[Power BI semantic model and reports]
```

## Principles

1. **Schema-first:** `schema.md` is the contract for the 54 table and column definitions.
2. **One table, one format:** a table is assigned to exactly one physical representation.
3. **No format conversion chain:** generation creates files from in-memory rows; it never reads one exported format to make another.
4. **Reproducibility:** seed, reference time, table assignments and row counts are recorded in the manifest.
5. **Quality gates:** key, nullability, unique-index and referential checks run before export.
6. **Layer separation:** staging mirrors source shape; curated facts/dimensions implement reporting semantics.


## Business-domain quality layer

The generator now runs the original domain checks and a business-enrichment validation pass before export. See the [Business-Domain Enrichment Architecture](domain-realism-architecture.md), [Business-Domain Data Contracts](../modeling/business-domain-data-contracts.md), and [Safe Landing Refresh Runbook](../ingestion/landing-data-refresh-runbook.md).
