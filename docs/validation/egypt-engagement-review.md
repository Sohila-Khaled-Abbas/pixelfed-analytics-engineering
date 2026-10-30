# Egyptian engagement change review — 30 October 2026

Base reviewed: `41100046de2552ec35dc1a73c4f071e40ec4050c` (`main`). GitHub remained at this SHA at the final read-only check. No branches, commits, PRs, issues, settings or generated files were written to GitHub.

## Proposed behavior

- Keep the existing 54-table/555-column source contract and six native formats.
- Extend realistic Egyptian creator scenario settings with Cairo civil-hour sampling and transparent provenance.
- Prevent engagement before actor registration; constrain story views to valid actor/story lifetimes.
- Recheck primary/unique/composite/foreign keys and canonical user/profile identity on physical exports.
- Correct comment defect injection to use `comments.comment`.
- Add a separate auditable Silver cleaning and core galaxy build: eight dimensions, eight facts and one weighted post/tag bridge. Existing Power BI artifacts and reference SQL are not migrated.
- Extend README, domain/identity/null/cleaning/model guides and CI; use the implementation guide as the executable contract.

## Validation performed locally

Environment: Linux, Python 3.12.14. Full Windows/Python-version GitHub CI was not run because no remote changes were authorized.

| Check | Result |
|---|---|
| Automated suite | 27 passed, 2 skipped |
| Ruff lint | Passed |
| Ruff format | All 52 Python files formatted |
| Full scenario, seed 42, scale 1, cutoff 2026-10-29T21:00:00Z, raw noise enabled | 97,672 source rows, 54 tables, six formats |
| Full physical-export key/identity/lifecycle validation | Passed |
| Full Silver/Gold reconciliation | 97,672 retained; 0 quarantined; all modeled keys/grains/bridge weights valid |
| Full Gold core facts | 6,000 posts; 25,000 likes; 12,000 comments; 8,000 follows; 8,000 media; 1,000 stories; 4,000 story views; 2,000 bookmarks |
| CI-sized scenario, seed 999, scale 0.02 | 1,959 rows; export and galaxy build passed |
| Independent stream smoke | 10,000 events, 2,000 stream profiles; passed |
| Corrupted existing user ID in exported comments | Rejected despite unchanged file shape and row counts |
| Unsafe floating-point identifier | Rejected |
| Malformed timestamp/quarantined parent | Cleaner tests preserve audit/reconciliation and remove dependent modeled events |
| Event before actor registration | Rejected |
| XLSX omitted trailing blank cells | Retained as logical nulls |

Two existing optional tests skipped because the repository's active `data/landing` was deliberately not generated/changed. Separate temporary candidate folders exercised physical export validation and the full analytics build. Generation fingerprints, source quality metadata and analytics reports accompany this review package.

## Limits and review decisions

All account/event records remain synthetic. CAPMAS population is a reference prior; language, disclosure, activity intensity and timing distributions remain explicit hypotheses, not observed market statistics. Population/digital-access sources do not prove platform audience composition.

The executable Gold build covers core social engagement. Remaining operational tables receive staging normalization only. It is not a fully modeled 54-table warehouse, does not add commerce or financial metrics and does not automatically change the saved Power BI project. The relational and independent stream identity namespaces are not interchangeable.

The active main ruleset requires a PR and prohibits deletion/non-fast-forward updates, with no bypass actors. The required-status-check list was empty when inspected. Do not edit this protection as part of this change. After approval, use a feature branch/PR and inspect the entire existing CI matrix before considering merge.

## Approval requested

Approve publishing the reviewed patch to a new feature branch and opening a PR against main. This does not authorize merging, changing branch protections or promoting generated landing data. Re-fetch and revalidate if main changes before publication.
