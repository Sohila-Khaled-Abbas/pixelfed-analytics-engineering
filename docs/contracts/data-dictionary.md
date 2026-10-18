# Data Dictionary

**Source contract:** `schema.md` · **Tables:** 54 · **Column definitions:** 555

This dictionary mirrors the supplied schema Markdown. The field `storage_format` describes the one format used for each generated table; it is not inferred from MySQL.

## `account_logs`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `item_id` | `bigint` | Yes |  |
| `item_type` | `varchar` | Yes |  |
| `action` | `varchar` | Yes |  |
| `message` | `varchar` | Yes |  |
| `link` | `varchar` | Yes |  |
| `ip_address` | `varchar` | Yes |  |
| `user_agent` | `varchar` | Yes |  |
| `metadata` | `json` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `activities`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `to_id` | `bigint` | Yes |  |
| `from_id` | `bigint` | Yes |  |
| `object_type` | `varchar` | Yes |  |
| `data` | `json` | Yes |  |
| `processed_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `avatars`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No | Unique |
| `media_path` | `varchar` | Yes |  |
| `thumb_path` | `varchar` | Yes |  |
| `remote_url` | `varchar` | Yes | Indexed |
| `change_count` | `int` | No |  |
| `last_fetched_at` | `timestamp` | Yes |  |
| `last_processed_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |

## `bookmarks`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `status_id` | `bigint` | No |  |
| `profile_id` | `bigint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `circle_profiles`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `owner_id` | `bigint` | Yes | Indexed |
| `circle_id` | `bigint` | No | Indexed |
| `profile_id` | `bigint` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `circles`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No | Indexed |
| `name` | `varchar` | Yes |  |
| `description` | `text` | Yes |  |
| `scope` | `varchar` | No |  |
| `bcc` | `tinyint` | No |  |
| `active` | `tinyint` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `collection_items`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `collection_id` | `bigint` | No | Indexed |
| `order` | `int` | Yes |  |
| `object_type` | `varchar` | No | Indexed |
| `object_id` | `bigint` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `collections`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | Yes |  |
| `title` | `varchar` | Yes |  |
| `description` | `text` | Yes |  |
| `is_nsfw` | `tinyint` | No |  |
| `visibility` | `varchar` | No | Indexed |
| `published_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `comments`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No |  |
| `user_id` | `bigint` | Yes |  |
| `status_id` | `bigint` | No |  |
| `comment` | `text` | Yes |  |
| `rendered` | `text` | Yes |  |
| `entities` | `json` | Yes |  |
| `is_remote` | `tinyint` | No |  |
| `rendered_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `contacts`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `response_requested` | `tinyint` | No |  |
| `message` | `text` | No |  |
| `response` | `text` | No |  |
| `read_at` | `timestamp` | Yes |  |
| `responded_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `direct_messages`

- **Storage format:** `json`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `to_id` | `bigint` | No | Indexed |
| `from_id` | `bigint` | No | Indexed |
| `from_profile_ids` | `varchar` | Yes |  |
| `group_message` | `tinyint` | No |  |
| `status_id` | `bigint` | No |  |
| `read_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `discover_categories`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `name` | `varchar` | Yes |  |
| `slug` | `varchar` | No | Unique |
| `active` | `tinyint` | No | Indexed |
| `order` | `tinyint` | No |  |
| `media_id` | `bigint` | Yes | Unique |
| `no_nsfw` | `tinyint` | No |  |
| `local_only` | `tinyint` | No |  |
| `public_only` | `tinyint` | No |  |
| `photos_only` | `tinyint` | No |  |
| `active_until` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `discover_category_hashtags`

- **Storage format:** `json`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `discover_category_id` | `bigint` | No | Indexed |
| `hashtag_id` | `bigint` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `email_verifications`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No |  |
| `email` | `varchar` | Yes |  |
| `user_token` | `varchar` | No | Indexed |
| `random_token` | `varchar` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `failed_jobs`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `connection` | `text` | No |  |
| `queue` | `text` | No |  |
| `payload` | `longtext` | No |  |
| `exception` | `longtext` | No |  |
| `failed_at` | `timestamp` | No |  |

## `follow_requests`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `follower_id` | `bigint` | No | Indexed |
| `following_id` | `bigint` | No | Indexed |
| `is_rejected` | `tinyint` | No |  |
| `is_local` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `followers`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `profile_id` | `bigint` | No |  |
| `following_id` | `bigint` | No |  |
| `local_profile` | `tinyint` | No | Indexed |
| `local_following` | `tinyint` | No | Indexed |
| `created_at` | `timestamp` | Yes | Indexed |
| `updated_at` | `timestamp` | Yes |  |

## `hashtag_follows`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `profile_id` | `bigint` | No | Indexed |
| `hashtag_id` | `bigint` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `hashtags`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `name` | `varchar` | No | Unique |
| `slug` | `varchar` | No | Unique |
| `is_nsfw` | `tinyint` | No |  |
| `is_banned` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `import_datas`

- **Storage format:** `json`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `profile_id` | `bigint` | No |  |
| `job_id` | `bigint` | Yes |  |
| `service` | `varchar` | No |  |
| `path` | `varchar` | Yes |  |
| `stage` | `tinyint` | No |  |
| `original_name` | `varchar` | Yes |  |
| `import_accepted` | `tinyint` | Yes |  |
| `completed_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `import_jobs`

- **Storage format:** `json`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `profile_id` | `bigint` | No |  |
| `service` | `varchar` | No |  |
| `uuid` | `varchar` | Yes |  |
| `storage_path` | `varchar` | Yes |  |
| `stage` | `tinyint` | No |  |
| `media_json` | `text` | Yes |  |
| `completed_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `instances`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `domain` | `varchar` | No | Unique |
| `url` | `varchar` | Yes |  |
| `name` | `varchar` | Yes |  |
| `admin_url` | `varchar` | Yes |  |
| `limit_reason` | `varchar` | Yes |  |
| `unlisted` | `tinyint` | No |  |
| `auto_cw` | `tinyint` | No |  |
| `banned` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `jobs`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `queue` | `varchar` | No | Indexed |
| `payload` | `longtext` | No |  |
| `attempts` | `tinyint` | No |  |
| `reserved_at` | `int` | Yes |  |
| `available_at` | `int` | No |  |
| `created_at` | `int` | No |  |

## `likes`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No |  |
| `status_id` | `bigint` | No |  |
| `flagged` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes | Indexed |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |

## `media`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `status_id` | `bigint` | Yes |  |
| `profile_id` | `bigint` | Yes |  |
| `user_id` | `bigint` | Yes | Indexed |
| `is_nsfw` | `tinyint` | No |  |
| `remote_media` | `tinyint` | No |  |
| `original_sha256` | `varchar` | Yes | Indexed |
| `optimized_sha256` | `varchar` | Yes | Indexed |
| `media_path` | `varchar` | No |  |
| `thumbnail_path` | `varchar` | Yes |  |
| `cdn_url` | `varchar` | Yes |  |
| `optimized_url` | `varchar` | Yes |  |
| `thumbnail_url` | `varchar` | Yes |  |
| `remote_url` | `varchar` | Yes |  |
| `caption` | `varchar` | Yes |  |
| `hls_path` | `varchar` | Yes |  |
| `order` | `tinyint` | No |  |
| `mime` | `varchar` | Yes |  |
| `size` | `int` | Yes |  |
| `orientation` | `varchar` | Yes |  |
| `filter_name` | `varchar` | Yes |  |
| `filter_class` | `varchar` | Yes |  |
| `license` | `varchar` | Yes |  |
| `processed_at` | `timestamp` | Yes |  |
| `hls_transcoded_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |
| `key` | `varchar` | Yes |  |
| `metadata` | `json` | Yes |  |
| `version` | `tinyint` | No |  |

## `mentions`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `status_id` | `bigint` | No |  |
| `profile_id` | `bigint` | No |  |
| `local` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |

## `migrations`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `migration` | `varchar` | No |  |
| `batch` | `int` | No |  |

## `mod_logs`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `user_username` | `varchar` | Yes |  |
| `object_uid` | `bigint` | Yes | Indexed |
| `object_id` | `bigint` | Yes | Indexed |
| `object_type` | `varchar` | Yes | Indexed |
| `action` | `varchar` | Yes |  |
| `message` | `text` | Yes |  |
| `metadata` | `json` | Yes |  |
| `access_level` | `varchar` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `newsroom`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | Yes |  |
| `header_photo_url` | `varchar` | Yes |  |
| `title` | `varchar` | Yes |  |
| `slug` | `varchar` | Yes | Unique |
| `category` | `varchar` | No |  |
| `summary` | `text` | Yes |  |
| `body` | `text` | Yes |  |
| `body_rendered` | `text` | Yes |  |
| `link` | `varchar` | Yes |  |
| `force_modal` | `tinyint` | No |  |
| `show_timeline` | `tinyint` | No |  |
| `show_link` | `tinyint` | No |  |
| `auth_only` | `tinyint` | No |  |
| `published_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `notifications`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No | Indexed |
| `actor_id` | `bigint` | Yes | Indexed |
| `item_id` | `bigint` | Yes |  |
| `item_type` | `varchar` | Yes |  |
| `action` | `varchar` | Yes |  |
| `message` | `varchar` | Yes |  |
| `rendered` | `varchar` | Yes |  |
| `read_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes | Indexed |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |

## `oauth_access_tokens`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `varchar` | No | PK |
| `user_id` | `bigint` | Yes | Indexed |
| `client_id` | `int` | No |  |
| `name` | `varchar` | Yes |  |
| `scopes` | `text` | Yes |  |
| `revoked` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `expires_at` | `datetime` | Yes |  |

## `oauth_auth_codes`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `varchar` | No | PK |
| `user_id` | `bigint` | No |  |
| `client_id` | `int` | No |  |
| `scopes` | `text` | Yes |  |
| `revoked` | `tinyint` | No |  |
| `expires_at` | `datetime` | Yes |  |

## `oauth_clients`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `user_id` | `bigint` | Yes | Indexed |
| `name` | `varchar` | No |  |
| `secret` | `varchar` | No |  |
| `redirect` | `text` | No |  |
| `personal_access_client` | `tinyint` | No |  |
| `password_client` | `tinyint` | No |  |
| `revoked` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `oauth_personal_access_clients`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `client_id` | `int` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `oauth_refresh_tokens`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `varchar` | No | PK |
| `access_token_id` | `varchar` | No | Indexed |
| `revoked` | `tinyint` | No |  |
| `expires_at` | `datetime` | Yes |  |

## `pages`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `root` | `varchar` | Yes | Indexed |
| `slug` | `varchar` | Yes | Unique |
| `title` | `varchar` | Yes |  |
| `category_id` | `int` | Yes | Indexed |
| `content` | `longtext` | Yes |  |
| `template` | `varchar` | No | Indexed |
| `active` | `tinyint` | No | Indexed |
| `cached` | `tinyint` | No | Indexed |
| `active_until` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `password_resets`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `email` | `varchar` | No | Indexed |
| `token` | `varchar` | No |  |
| `created_at` | `timestamp` | Yes |  |

## `places`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `slug` | `varchar` | No | Indexed |
| `name` | `varchar` | No | Indexed |
| `country` | `varchar` | No | Indexed |
| `aliases` | `json` | Yes |  |
| `lat` | `decimal` | Yes |  |
| `long` | `decimal` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `profile_sponsors`

- **Storage format:** `json`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No | Unique |
| `sponsors` | `json` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `profiles`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `int` | Yes |  |
| `domain` | `varchar` | Yes | Indexed |
| `username` | `varchar` | Yes | Indexed |
| `status` | `varchar` | Yes | Indexed |
| `name` | `varchar` | Yes |  |
| `bio` | `text` | Yes |  |
| `unlisted` | `tinyint` | No | Indexed |
| `cw` | `tinyint` | No | Indexed |
| `no_autolink` | `tinyint` | No | Indexed |
| `location` | `varchar` | Yes |  |
| `website` | `varchar` | Yes |  |
| `profile_layout` | `varchar` | Yes |  |
| `header_bg` | `varchar` | Yes |  |
| `post_layout` | `varchar` | Yes |  |
| `is_private` | `tinyint` | No |  |
| `sharedInbox` | `varchar` | Yes | Indexed |
| `inbox_url` | `varchar` | Yes |  |
| `outbox_url` | `varchar` | Yes |  |
| `key_id` | `varchar` | Yes | Unique |
| `follower_url` | `varchar` | Yes |  |
| `following_url` | `varchar` | Yes |  |
| `private_key` | `text` | Yes |  |
| `public_key` | `text` | Yes |  |
| `remote_url` | `varchar` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |
| `delete_after` | `timestamp` | Yes |  |
| `is_suggestable` | `tinyint` | No | Indexed |
| `last_fetched_at` | `timestamp` | Yes |  |
| `status_count` | `int` | Yes |  |
| `followers_count` | `int` | Yes |  |
| `following_count` | `int` | Yes |  |
| `webfinger` | `varchar` | Yes | Unique |
| `avatar_url` | `varchar` | Yes |  |

## `report_comments`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `report_id` | `bigint` | No | Indexed |
| `profile_id` | `bigint` | No |  |
| `user_id` | `bigint` | No |  |
| `comment` | `text` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `report_logs`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `profile_id` | `bigint` | No |  |
| `item_id` | `bigint` | Yes |  |
| `item_type` | `varchar` | Yes |  |
| `action` | `varchar` | Yes |  |
| `system_message` | `tinyint` | No |  |
| `metadata` | `json` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `reports`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No |  |
| `user_id` | `bigint` | Yes |  |
| `object_id` | `bigint` | No |  |
| `object_type` | `varchar` | Yes |  |
| `reported_profile_id` | `bigint` | Yes |  |
| `type` | `varchar` | Yes |  |
| `message` | `varchar` | Yes |  |
| `admin_seen` | `timestamp` | Yes |  |
| `not_interested` | `tinyint` | No |  |
| `spam` | `tinyint` | No |  |
| `nsfw` | `tinyint` | No |  |
| `abusive` | `tinyint` | No |  |
| `meta` | `json` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `sessions`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `varchar` | No | Unique |
| `user_id` | `bigint` | Yes |  |
| `ip_address` | `varchar` | Yes |  |
| `user_agent` | `text` | Yes |  |
| `payload` | `text` | No |  |
| `last_activity` | `int` | No |  |

## `status_hashtags`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `status_id` | `bigint` | No | Indexed |
| `hashtag_id` | `bigint` | No | Indexed |
| `profile_id` | `bigint` | Yes | Indexed |
| `status_visibility` | `varchar` | Yes | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `statuses`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `uri` | `varchar` | Yes | Unique |
| `caption` | `text` | Yes |  |
| `rendered` | `text` | Yes |  |
| `profile_id` | `bigint` | Yes | Indexed |
| `type` | `varchar` | Yes | Indexed |
| `in_reply_to_id` | `bigint` | Yes |  |
| `reblog_of_id` | `bigint` | Yes |  |
| `url` | `varchar` | Yes |  |
| `is_nsfw` | `tinyint` | No | Indexed |
| `scope` | `varchar` | No | Indexed |
| `visibility` | `enum` | No | Indexed |
| `reply` | `tinyint` | No |  |
| `likes_count` | `bigint` | No |  |
| `reblogs_count` | `bigint` | No |  |
| `language` | `varchar` | Yes |  |
| `conversation_id` | `bigint` | Yes |  |
| `local` | `tinyint` | No | Indexed |
| `application_id` | `bigint` | Yes |  |
| `in_reply_to_profile_id` | `bigint` | Yes |  |
| `entities` | `json` | Yes |  |
| `created_at` | `timestamp` | Yes | Indexed |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |
| `cw_summary` | `varchar` | Yes |  |
| `reply_count` | `int` | Yes |  |
| `comments_disabled` | `tinyint` | No |  |
| `place_id` | `bigint` | Yes | Indexed |
| `object_url` | `varchar` | Yes | Unique |

## `stories`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | No | Indexed |
| `type` | `varchar` | Yes |  |
| `size` | `int` | Yes |  |
| `mime` | `varchar` | Yes |  |
| `duration` | `smallint` | No |  |
| `path` | `varchar` | Yes |  |
| `cdn_url` | `varchar` | Yes |  |
| `public` | `tinyint` | No | Indexed |
| `local` | `tinyint` | No | Indexed |
| `view_count` | `int` | Yes |  |
| `comment_count` | `int` | Yes |  |
| `story` | `json` | Yes |  |
| `expires_at` | `timestamp` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `story_views`

- **Storage format:** `csv_gz`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `story_id` | `bigint` | No | Indexed |
| `profile_id` | `bigint` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `user_devices`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `ip` | `varchar` | No | Indexed |
| `user_agent` | `varchar` | No | Indexed |
| `fingerprint` | `varchar` | Yes |  |
| `name` | `varchar` | Yes |  |
| `trusted` | `tinyint` | Yes |  |
| `last_active_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `user_filters`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `filterable_id` | `bigint` | No |  |
| `filterable_type` | `varchar` | No |  |
| `filter_type` | `varchar` | No | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `user_invites`

- **Storage format:** `sqlite`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Indexed |
| `profile_id` | `bigint` | No | Indexed |
| `email` | `varchar` | No | Unique |
| `message` | `text` | Yes |  |
| `key` | `varchar` | No |  |
| `token` | `varchar` | No |  |
| `valid_until` | `timestamp` | Yes |  |
| `used_at` | `timestamp` | Yes | Indexed |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |

## `user_settings`

- **Storage format:** `xlsx`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `user_id` | `bigint` | No | Unique |
| `role` | `varchar` | No |  |
| `crawlable` | `tinyint` | No |  |
| `show_guests` | `tinyint` | No |  |
| `show_discover` | `tinyint` | No |  |
| `public_dm` | `tinyint` | No |  |
| `hide_cw_search` | `tinyint` | No |  |
| `hide_blocked_search` | `tinyint` | No |  |
| `always_show_cw` | `tinyint` | No |  |
| `compose_media_descriptions` | `tinyint` | No |  |
| `reduce_motion` | `tinyint` | No |  |
| `optimize_screen_reader` | `tinyint` | No |  |
| `high_contrast_mode` | `tinyint` | No |  |
| `video_autoplay` | `tinyint` | No |  |
| `send_email_new_follower` | `tinyint` | No |  |
| `send_email_new_follower_request` | `tinyint` | No |  |
| `send_email_on_share` | `tinyint` | No |  |
| `send_email_on_like` | `tinyint` | No |  |
| `send_email_on_mention` | `tinyint` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `show_profile_followers` | `tinyint` | No |  |
| `show_profile_follower_count` | `tinyint` | No |  |
| `show_profile_following` | `tinyint` | No |  |
| `show_profile_following_count` | `tinyint` | No |  |

## `users`

- **Storage format:** `csv`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `bigint` | No | PK |
| `profile_id` | `bigint` | Yes | Unique |
| `name` | `varchar` | Yes |  |
| `username` | `varchar` | Yes | Unique |
| `email` | `varchar` | No | Unique |
| `status` | `varchar` | Yes | Indexed |
| `language` | `varchar` | Yes | Indexed |
| `password` | `varchar` | No |  |
| `remember_token` | `varchar` | Yes |  |
| `is_admin` | `tinyint` | No |  |
| `email_verified_at` | `timestamp` | Yes |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
| `deleted_at` | `timestamp` | Yes | Indexed |
| `2fa_enabled` | `tinyint` | No |  |
| `2fa_secret` | `varchar` | Yes |  |
| `2fa_backup_codes` | `json` | Yes |  |
| `2fa_setup_at` | `timestamp` | Yes |  |
| `delete_after` | `timestamp` | Yes |  |

## `websockets_statistics_entries`

- **Storage format:** `jsonl`
- **Rows (full default run):** from `data/landing/metadata/row_counts.csv`

| Column | MySQL type | Nullable | Key / index |
|---|---|---:|---|
| `id` | `int` | No | PK |
| `app_id` | `varchar` | No |  |
| `peak_connection_count` | `int` | No |  |
| `websocket_message_count` | `int` | No |  |
| `api_message_count` | `int` | No |  |
| `created_at` | `timestamp` | Yes |  |
| `updated_at` | `timestamp` | Yes |  |
