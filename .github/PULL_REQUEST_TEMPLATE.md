## Description

Provide a clear and concise summary of the changes made in this Pull Request.

- **Type of Change:**
  - [ ] Data Contract / Schema Update (`schema.md`, `config/`)
  - [ ] Lakehouse Ingestion / Generation Logic (`src/`)
  - [ ] Dimensional Modeling / Semantic Layer (`database/`, `powerbi/`)
  - [ ] Automated Quality Tests (`tests/`)
  - [ ] Documentation & Playbooks (`docs/`)
  - [ ] CI/CD & Repository Infrastructure (`.github/`)

## Related Issues

Fixes #(issue)

## Analytics Engineering Checklist

- [ ] **Schema Fidelity**: Does the change strictly preserve canonical table/column names and ordering?
- [ ] **One-Format Rule**: Is every table assigned to exactly one native physical format without synthetic duplication?
- [ ] **Reproducibility**: Are synthetic seeds and `as_of` temporal reference timestamps preserved?
- [ ] **Dimensional Grain**: If modeling is affected, is the natural business grain preserved (no fan-out joins)?
- [ ] **Nullability & Key Tests**: Have primary key uniqueness and foreign key integrity constraints been validated?
- [ ] **Testing**: Did `pytest` pass with 100% success rate across all test suites?
- [ ] **Validation Script**: Did `python src/validate_landing.py` run without errors?
- [ ] **Documentation**: Are related documents in `docs/` and `README.md` updated?

## Verification Output

```text
Paste terminal output from `pytest` and `validate_landing.py` here
```
