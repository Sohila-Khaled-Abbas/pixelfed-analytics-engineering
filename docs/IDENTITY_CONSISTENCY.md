# PixelFed Identity Consistency and ID Semantics

## Why this matters

The earlier generator selected some `user_id` and `profile_id` values independently even when both columns described the same actor. A row could therefore refer to one profile and a different local user. The updated generator resolves these fields from canonical entity maps after generating the source rows, then validates the links before writing files.

## Correct key semantics

| Column | Meaning | Must reference |
|---|---|---|
| `users.id` | Local account/user primary key | `users` row |
| `users.profile_id` | Profile belonging to that account | `profiles.id` |
| `profiles.id` | Profile primary key | `profiles` row |
| `profiles.user_id` | Local account that owns this profile; nullable for remote profiles | `users.id` |
| `comments.profile_id` | Comment author profile | `profiles.id` |
| `comments.user_id` | Local user owning the comment author profile; nullable for a remote profile | `users.id` |
| `media.status_id` | Status to which media is attached | `statuses.id` |
| `media.profile_id` | Profile that authored the attached status/media | `profiles.id` |
| `media.user_id` | Local user owning that profile; null for a remote profile | `users.id` |
| `reports.profile_id` / `reports.user_id` | Reporter profile and corresponding local account | `profiles.id` / `users.id` |
| `report_comments.profile_id` / `report_comments.user_id` | Commenter's profile and corresponding local account | `profiles.id` / `users.id` |
| `status_hashtags.profile_id` | Author profile of the associated status | `profiles.id` |
| `follow_requests.follower_id`, `following_id` | Request sender and target profiles | `profiles.id` |

**Do not join `users.id` directly to `profiles.id` just because the numbers happen to look equal.** Those are primary keys from different tables. The relationship is carried by `profiles.user_id` and `users.profile_id`. Relational databases can have overlapping primary-key values in different tables without a conflict.

## How identities are generated

- IDs are deterministic table primary keys; for the same schema and scale, row keys remain stable.
- A local account's display name and username are generated once from a seeded persona and copied to its linked profile rather than generated independently. The associated email uses the reserved `example.test` domain.
- There are 1,000 local `users` and 1,200 `profiles` at full scale. The first 1,000 profiles are linked one-to-one to local accounts; the remaining 200 represent federated/remote profiles with `profiles.user_id = null` and a synthetic remote domain. This avoids inventing a local user record for a remote Fediverse profile.
- Comments/reports link their `user_id` to the owner of their `profile_id`. Media attached to a status uses that status author's profile and corresponding user if local. Status-hashtag bridge rows use the linked status author.
- `statuses.likes_count`, `reply_count`, and `reblogs_count` are derived from generated like/reply/reblog event rows; profile status/follower/following counters are derived from their corresponding rows.
- `updated_at` and processing/rendering timestamps are adjusted so they do not precede `created_at`.
- The generator's data-quality report checks FK integrity, the user/profile link in both directions, paired actor IDs, status/media author alignment, and unique keys.

## Known semantic correction

The supplied Markdown relationship section states `followers.id → follow_requests.follower_id`. This is likely a relationship-inference error: `followers.id` identifies one follow-edge row, whereas `follow_requests.follower_id` identifies the requesting profile. The generator applies a semantic override for this single relationship and maps it to `profiles.id`. The original schema file's column definitions are preserved, and the effective relationship is recorded in `metadata/schema_contract.json`.

## Synthetic versus real data

These records are still synthetic; a schema contains table and column definitions, not the original production records or IDs. The updated generator creates plausible, repeatable, referentially consistent training data. If the project must use actual PixelFed account IDs and actual records, use an authorized database export or a source API that legitimately provides those records. No real account identifiers are fabricated or inferred from the schema.

## Validate locally

After generation, inspect `data/landing/metadata/data_quality_report.json` for the `identity_consistency` section and `passed: true`. Run `python src/validate_landing.py` against the landing folder. The validator checks schema shape, row counts, exactly one storage format per table and SQLite integrity. The unit suite also tests bidirectional user/profile links and actor-to-profile consistency.
