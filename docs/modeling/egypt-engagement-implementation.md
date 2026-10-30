# Egyptian creator engagement: executable source → Silver → galaxy

This is a synthetic Egyptian visual-content community, with local creator/business profiles and federated participants. Business question: **which content themes attract participation, how long does engagement take, and how does optional disclosure affect analysis?** It is not a sales, revenue, or nationally representative audience dataset.

## Evidence and assumptions

| Input | Evidence date / review | Permitted use | Limitation |
|---|---|---|---|
| CAPMAS governorate urban/rural estimates | 1 January 2024; source checked 30 October 2026 | The checked-in 27-governorate reference totals 105,914,499 residents | A geographic sampling prior, not a distribution of platform accounts |
| World Bank WDI IT.NET.USER.ZS / ITU | 2024; source checked 30 October 2026 | Digital-access context; page displays a rounded 75% | Do not apply a national percentage as a per-profile observation |
| `config/egypt_market_profile.json` | Versioned scenario settings | Urban propensity, disclosure rates, Arabic/English mixture, creator share, topic stickiness, Cairo hourly activity weights | These are hypotheses, not observed Egyptian platform statistics |
| PixelFed-inspired `schema.md` | 54 tables / 555 columns | Operational source contract | Neither production data nor real account IDs |

Primary references:

- CAPMAS: https://www.capmas.gov.eg/Admin/Pages%20Files/20245121324361-%20pop_new.pdf
- World Bank / ITU: https://data.worldbank.org/indicator/IT.NET.USER.ZS?locations=EG

The existing DataReportal link remains secondary market context; it does not calibrate accounts, engagement or language. No scraping or personal account imports are introduced. Bilingual text is authored simulation content. Names are fictional; contact URLs use reserved domains. Fine-grained coordinates stay missing when unverified. No EGP measures can be inferred from this schema.

For sensitivity analysis, compare the urban-propensity factor at 0 and 0.35, then language/disclosure assumptions separately, with the same seed/cutoff. Changing the profile changes the scenario: do not compare outputs as measured market trends.

## Review findings addressed

1. Export validation previously checked file shape/counts and SQLite relationships, without validating all cross-format IDs. `landing_contracts.py` now loads all six formats and checks primary, unique/composite, foreign and paired actor keys after serialization.
2. Event sampling could precede actor registration. Likes, comments and bookmarks now start after both actor and post creation. Story-viewer sampling respects registration and story expiry. Moderation reports also start after reporter/target creation. Deleted timestamps cannot precede creation. Core event lifecycle checks run in memory and on exported data.
3. Hour weights previously applied directly to UTC. They now apply on the `Africa/Cairo` calendar, then return UTC source timestamps. DST is resolved by IANA timezone data; source timestamps are never relabelled as Cairo time.
4. Controlled comment defects targeted nonexistent `comments.reply`. They now target `comments.comment`.
5. The existing model guides and SQL DDL were design/reference material. `build_analytics.py` supplies a separately validated core engagement implementation with dimensions, eight facts and a weighted bridge.

## Reproduce locally (PowerShell, repository root)

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m ruff format --check .

python src/generate_landing.py --scale 0.03 --seed 42 --as-of 2026-10-29T21:00:00Z --raw-quality --output-dir ./data/egypt_review_candidate
python src/validate_landing.py --landing ./data/egypt_review_candidate
python src/build_analytics.py --landing ./data/egypt_review_candidate --output ./data/egypt_review_analytics
```

Use scale 1 for the full scenario. Choose fresh output paths: the analytics builder refuses overwrites. These commands do not promote or replace `data/landing`. The existing `refresh_landing.py` candidate/backup/promote workflow is unchanged. Review generated reports before any deliberate promotion.

Generation records hashes of the Python source, schema, market profile and governorate reference, dependency versions, seed, scale and UTC cutoff. The analytics report records a source-manifest SHA-256. Reproduction requires the same inputs and dependency/timezone versions; a seed alone does not guarantee byte-identical ZIP/XLSX or compressed files across environments. The activity-stream generator has its own identity universe; do not join stream profile numbers to relational profiles. Cross-source matching needs an explicit governed mapping.

## Identity contract

- Keep table-scoped IDs exactly. `users.id` and `profiles.id` are different entity keys, even when numbers overlap.
- Join `users.profile_id → profiles.id` and `profiles.user_id → users.id`; verify both directions.
- Local profiles have a user and no remote domain. Federated profiles have a domain and no local user. Do not invent local accounts for them.
- `comments`, `media`, `reports` and `report_comments` paired user/profile IDs must identify the same actor.
- Media attached to a post and status-hashtag author fields inherit the post author. `follow_requests.follower_id` references profiles, using the existing documented schema override.
- Do not use row indices generated independently in each query as dimension keys. The executable single-source Type-1 model uses source IDs as deterministic text keys. It has no historical SCD2 claims.
- Gold key `"0"` represents unknown/not applicable. `is_local = false` distinguishes a remote profile's inapplicable user key from an unknown profile. Source IDs are never rewritten to zero. Known IDs with broken relationships fail validation.
- IDs are never parsed through floating point. Unsafe float identifiers above the exact integer range are rejected. Keep identifiers as text in Power Query/Power BI.

## Cleaning and null policy

Bronze is immutable. The cleaner writes separate JSONL files and retains quarantined rows with source table, ID, reasons and original record.

| Field/state | Silver action | Gold/KPI interpretation |
|---|---|---|
| PK/FK absent or unknown | Required/malformed keys and broken references fail source validation | Never infer identity by name, email or row position |
| Federated `profiles.user_id` | Preserve null | No local user; not a data defect |
| Optional biography, caption, website, location | Trim free text, change optional blank strings to null | Missing flags/disclosure flags; no fabricated text |
| Required empty text, e.g. unanswered `contacts.response` | Preserve empty text; source NOT NULL is distinct from semantic completeness | Model response state from `responded_at`; no fake response |
| ISO timestamp / intentional `YYYY/MM/DD HH:MM:SS` | Explicit parsing; naive source timestamps mean UTC | UTC plus Cairo offset/local date/time in facts |
| Missing core event timestamp/actor | Quarantine from event facts | Exclude undated events from time-based denominators and report exclusions |
| Invalid timestamp | Core event timestamp errors fail strict landing validation; cleaner also records invalid date rows when processing admissible staging data | No replacement with today, 1900 or account registration time |
| Nullable attached post for media | Preserve null | Unattached upload is valid; no artificial post |
| Missing numeric measure | Preserve null | Zero only when an observed count is actually zero |
| Missing place coordinates | Preserve null | Do not geocode to a guessed neighborhood or (0,0) |
| Duplicate source PK / unique tuple | Fail source validation | Never silently choose a survivor |
| Duplicate status-hashtag pair | Source uniqueness is checked; bridge construction also uses distinct pairs | Exactly one row per post/tag; weights sum to 1 per tagged post |

Cleaning runs for all 54 staging tables, but only the listed engagement tables receive Gold modeling. The Silver projection normalizes timestamps/free text; it does not promise every operational JSON payload or numeric field has been fully modeled. Secret/authentication/operational tables remain outside Gold. Do not load those tables into a public report.

If a parent post/story is quarantined, dependent core event rows and post-tag links are also quarantined. Other operational staging references may still point at that quarantined record; Silver is staging, not a fully constrained warehouse. The Gold dimension/relationship gates guarantee the modeled subset has no orphan keys. Input rows = retained Silver rows + quarantined rows. A passing build may have quarantined rows: inspect the audit count before interpreting coverage.

## Dimensions, facts and bridges

The executable JSONL outputs use the following names. The older plural SQL DDL and existing hand-built Power BI project are reference/legacy artifacts; this change does not migrate or deploy that semantic model automatically.

| Output | Grain / rule |
|---|---|
| `dim_user` | One local source user, plus reserved unknown row; no contact details |
| `dim_profile` | One source profile, plus unknown; local/federated ownership and disclosure flags |
| `dim_post` | One retained status; language, type, scope and caption missingness |
| `dim_story` | One retained story; author profile key |
| `dim_hashtag` | One source hashtag |
| `dim_place` | One source place, plus unknown; coordinates retain source precision |
| `dim_date` | Complete Cairo calendar from earliest to latest retained core event; Friday/Saturday weekend |
| `dim_time` | All 1,440 Cairo clock minutes; source UTC timestamp/offset retained in facts |
| `fct_post` | One retained status, including status subtypes; filter type/reply/reblog rules before calling it an original publication |
| `fct_like` | One source like event; `is_deleted` supports current-active versus historical-created definitions |
| `fct_comment` | One source comment; null comment length remains null |
| `fct_follow` | One current source follow-edge record; not a complete follow/unfollow history |
| `fct_media` | One source media asset; attached post may be null |
| `fct_story` | One retained story |
| `fct_story_view` | One source story-viewer record; not repeat impressions or independently verified reach |
| `fct_bookmark` | One source bookmark record |
| `bridge_post_hashtag` | Distinct post/tag pair; allocation weight `1 / distinct tags on post` |

Fact role keys: `profile_key` is the acting/viewing profile, `author_profile_key` is the target content author, and `following_profile_key` is the follow target. These roles must not be merged into a single ambiguous filter path.

## Galaxy relationship plan for Power BI

Use the Gold JSONL files from a single build. Create one-to-many, single-direction filters from dimensions to each fact. All post-bearing facts share `dim_post`, not fact-to-fact relationships. All facts share local date/time dimensions. Use role-playing copies of `dim_profile` for actor, author and follow target (or inactive relationships with explicit DAX). `dim_user` may filter the profile dimension for account-level analysis; do not add redundant direct paths to the same facts.

For hashtags, relate `dim_hashtag → bridge_post_hashtag` and use a bridge-aware measure/TREATAS to filter `dim_post`. Avoid enabling global bidirectional relationships. A post with three tags must not count as three posts when totaling the entire model. Weights support allocated-post counts only for tagged posts; untagged posts require a separate untagged bucket or coverage measure. Do not apply post-allocation weights blindly to engagement facts without an explicit post-grain aggregation.

`dim_place` describes an explicit post tag; a missing tag is not evidence of a non-Egyptian author. A profile's disclosed location is not inferred from its content location. The private simulated governorate assignment is not promoted to a claimed observed profile attribute.

Suggested measures:

- Posts: distinct `fct_post[post_key]`, with an explicitly stated publication/subtype/deletion scope.
- Created likes: count of `fct_like`; active likes: exclude `is_deleted = true`.
- Comments: count of comment events, independently from nullable comment text.
- Content engagement: likes + comments + bookmarks, labeled as those events; not reach or conversion rate.
- Engagement per post: events for the same post cohort / posts in that cohort. Event date and post-publication date answer different questions.
- Disclosure rate: profiles with disclosed location / known profiles, excluding unknown key 0. Never count remote absence of user IDs as missing local identities.
- Hashtag-attributed posts: sum allocation weights over the bridge, with tagged-post coverage disclosed.

The source `statuses.reply_count` counts status reply rows, not the separate `comments` table. Do not reconcile those as if they were the same event system. Counter checks run before intentionally injected raw text defects. Bronze report `passed` describes pre-injection domain validity; physical-export gates recheck relationships and core chronology afterward.

## Power Query GUI path

1. Duplicate/reference the imported Bronze queries into a Silver query group; disable load for raw operational/authentication tables.
2. Assign IDs **Text**, not Decimal Number. Preserve `profile_id` and `user_id` separately. Check distinct primary keys before merges.
3. Apply Trim to nullable free text; replace optional empty strings with null. Keep raw columns when reviewing changes. Do not fill down IDs or all-null columns.
4. Parse ISO and documented slash timestamps explicitly. Keep errors in a separate audit query; do not choose Remove Errors without counting and explaining exclusions.
5. Merge comments/media/reports to profiles on `profile_id`, then compare the existing `user_id` with the profile's owning user. Anti-join to find orphan IDs; mismatch must block promotion.
6. Create the dimensions and facts at the exact grains above. Use `dim_post` as the shared content dimension. Derive Cairo local calendar fields with timezone-aware preprocessing; a fixed UTC+2 Power Query offset fails during daylight saving time.
7. Group status-hashtag pairs distinctly, count tags per post, then calculate allocation weights. Verify sums of 1 for tagged posts.
8. Import only reviewed Gold outputs and confirm one-to-many relationship cardinalities. Check source/retained/quarantine reconciliation before building visuals.

## Validation and GitHub workflow

Run Ruff, pytest, generation, physical export validation, then analytics build. Tests deliberately corrupt an existing actor user ID without changing counts, reject unsafe float IDs, test quarantine dependency closure, preserve nulls and check bridge weights/Gold orphan rejection. CI adds a core galaxy smoke build after its existing landing check; the partitioned stream smoke check remains independent.

Read-only review found active ruleset `Protect main` (25352853): PR required, deletion/force push prohibited, no bypass actors. Its required-status-check list is empty; do not assume CI is enforced merely because a status-check rule exists. The existing CI matrix covers Python 3.10/3.11/3.12 on Linux and Windows. Local validation is one environment, not proof the full remote matrix passed.

No GitHub writes are authorized by preparing this change. After explicit approval: re-fetch `main`, rebase/revalidate if it moved, create a feature branch and PR, inspect all CI results, then request review/merge approval. Never disable protections, force-push `main`, or silently promote generated data.
