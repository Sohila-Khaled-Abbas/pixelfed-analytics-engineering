CREATE TABLE `account_logs`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `item_id` BIGINT NULL,
    `item_type` VARCHAR(255) NULL,
    `action` VARCHAR(255) NULL,
    `message` VARCHAR(255) NULL,
    `link` VARCHAR(255) NULL,
    `ip_address` VARCHAR(255) NULL,
    `user_agent` VARCHAR(255) NULL,
    `metadata` JSON NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `account_logs` ADD INDEX `account_logs_user_id_index`(`user_id`);
CREATE TABLE `activities`(
    `id` BIGINT NOT NULL,
    `to_id` BIGINT NULL,
    `from_id` BIGINT NULL,
    `object_type` VARCHAR(255) NULL,
    `data` JSON NULL,
    `processed_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `avatars`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `media_path` VARCHAR(255) NULL,
    `thumb_path` VARCHAR(255) NULL,
    `remote_url` VARCHAR(255) NULL,
    `change_count` INT NOT NULL,
    `last_fetched_at` TIMESTAMP NULL,
    `last_processed_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `avatars` ADD UNIQUE `avatars_profile_id_unique`(`profile_id`);
ALTER TABLE
    `avatars` ADD INDEX `avatars_remote_url_index`(`remote_url`);
ALTER TABLE
    `avatars` ADD INDEX `avatars_deleted_at_index`(`deleted_at`);
CREATE TABLE `bookmarks`(
    `id` INT NOT NULL,
    `status_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `bookmarks` ADD UNIQUE `bookmarks_status_id_profile_id_unique`(`status_id`, `profile_id`);
CREATE TABLE `circle_profiles`(
    `id` BIGINT NOT NULL,
    `owner_id` BIGINT NULL,
    `circle_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `circle_profiles` ADD UNIQUE `circle_profiles_circle_id_profile_id_unique`(`circle_id`, `profile_id`);
ALTER TABLE
    `circle_profiles` ADD INDEX `circle_profiles_owner_id_index`(`owner_id`);
ALTER TABLE
    `circle_profiles` ADD INDEX `circle_profiles_circle_id_index`(`circle_id`);
ALTER TABLE
    `circle_profiles` ADD INDEX `circle_profiles_profile_id_index`(`profile_id`);
CREATE TABLE `circles`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `name` VARCHAR(255) NULL,
    `description` TEXT NULL,
    `scope` VARCHAR(255) NOT NULL,
    `bcc` TINYINT NOT NULL,
    `active` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `circles` ADD INDEX `circles_profile_id_index`(`profile_id`);
ALTER TABLE
    `circles` ADD INDEX `circles_active_index`(`active`);
CREATE TABLE `collection_items`(
    `id` BIGINT NOT NULL,
    `collection_id` BIGINT NOT NULL,
    `order` INT NULL,
    `object_type` VARCHAR(255) NOT NULL,
    `object_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `collection_items` ADD INDEX `collection_items_collection_id_index`(`collection_id`);
ALTER TABLE
    `collection_items` ADD INDEX `collection_items_object_type_index`(`object_type`);
ALTER TABLE
    `collection_items` ADD INDEX `collection_items_object_id_index`(`object_id`);
CREATE TABLE `collections`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NULL,
    `title` VARCHAR(255) NULL,
    `description` TEXT NULL,
    `is_nsfw` TINYINT NOT NULL,
    `visibility` VARCHAR(255) NOT NULL,
    `published_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `collections` ADD INDEX `collections_visibility_index`(`visibility`);
CREATE TABLE `comments`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `user_id` BIGINT NULL,
    `status_id` BIGINT NOT NULL,
    `comment` TEXT NULL,
    `rendered` TEXT NULL,
    `entities` JSON NULL,
    `is_remote` TINYINT NOT NULL,
    `rendered_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `contacts`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `response_requested` TINYINT NOT NULL,
    `message` TEXT NOT NULL,
    `response` TEXT NOT NULL,
    `read_at` TIMESTAMP NULL,
    `responded_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `contacts` ADD INDEX `contacts_user_id_index`(`user_id`);
CREATE TABLE `direct_messages`(
    `id` BIGINT NOT NULL,
    `to_id` BIGINT NOT NULL,
    `from_id` BIGINT NOT NULL,
    `from_profile_ids` VARCHAR(255) NULL,
    `group_message` TINYINT NOT NULL,
    `status_id` BIGINT NOT NULL,
    `read_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `direct_messages` ADD UNIQUE `direct_messages_to_id_from_id_status_id_unique`(`to_id`, `from_id`, `status_id`);
ALTER TABLE
    `direct_messages` ADD INDEX `direct_messages_to_id_index`(`to_id`);
ALTER TABLE
    `direct_messages` ADD INDEX `direct_messages_from_id_index`(`from_id`);
CREATE TABLE `discover_categories`(
    `id` BIGINT NOT NULL,
    `name` VARCHAR(255) NULL,
    `slug` VARCHAR(255) NOT NULL,
    `active` TINYINT NOT NULL,
    `order` TINYINT NOT NULL,
    `media_id` BIGINT NULL,
    `no_nsfw` TINYINT NOT NULL,
    `local_only` TINYINT NOT NULL,
    `public_only` TINYINT NOT NULL,
    `photos_only` TINYINT NOT NULL,
    `active_until` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `discover_categories` ADD UNIQUE `discover_categories_slug_unique`(`slug`);
ALTER TABLE
    `discover_categories` ADD INDEX `discover_categories_active_index`(`active`);
ALTER TABLE
    `discover_categories` ADD UNIQUE `discover_categories_media_id_unique`(`media_id`);
CREATE TABLE `discover_category_hashtags`(
    `id` BIGINT NOT NULL,
    `discover_category_id` BIGINT NOT NULL,
    `hashtag_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `discover_category_hashtags` ADD UNIQUE `discover_category_id_hashtag_id_unique`(
        `discover_category_id`,
        `hashtag_id`
    );
ALTER TABLE
    `discover_category_hashtags` ADD INDEX `discover_category_hashtags_discover_category_id_index`(`discover_category_id`);
ALTER TABLE
    `discover_category_hashtags` ADD INDEX `discover_category_hashtags_hashtag_id_index`(`hashtag_id`);
CREATE TABLE `email_verifications`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `email` VARCHAR(255) NULL,
    `user_token` VARCHAR(255) NOT NULL,
    `random_token` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `email_verifications` ADD INDEX `email_verifications_user_token_index`(`user_token`);
ALTER TABLE
    `email_verifications` ADD INDEX `email_verifications_random_token_index`(`random_token`);
CREATE TABLE `failed_jobs`(
    `id` BIGINT NOT NULL,
    `connection` TEXT NOT NULL,
    `queue` TEXT NOT NULL,
    `payload` LONGTEXT NOT NULL,
    `exception` LONGTEXT NOT NULL,
    `failed_at` TIMESTAMP NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `follow_requests`(
    `id` BIGINT NOT NULL,
    `follower_id` BIGINT NOT NULL,
    `following_id` BIGINT NOT NULL,
    `is_rejected` TINYINT NOT NULL,
    `is_local` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `follow_requests` ADD INDEX `follow_requests_follower_id_index`(`follower_id`);
ALTER TABLE
    `follow_requests` ADD INDEX `follow_requests_following_id_index`(`following_id`);
CREATE TABLE `followers`(
    `id` INT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `following_id` BIGINT NOT NULL,
    `local_profile` TINYINT NOT NULL,
    `local_following` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `followers` ADD UNIQUE `followers_profile_id_following_id_unique`(`profile_id`, `following_id`);
ALTER TABLE
    `followers` ADD INDEX `followers_local_profile_index`(`local_profile`);
ALTER TABLE
    `followers` ADD INDEX `followers_local_following_index`(`local_following`);
ALTER TABLE
    `followers` ADD INDEX `followers_created_at_index`(`created_at`);
CREATE TABLE `hashtag_follows`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `hashtag_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `hashtag_follows` ADD UNIQUE `hashtag_follows_user_id_profile_id_hashtag_id_unique`(
        `user_id`,
        `profile_id`,
        `hashtag_id`
    );
ALTER TABLE
    `hashtag_follows` ADD INDEX `hashtag_follows_user_id_index`(`user_id`);
ALTER TABLE
    `hashtag_follows` ADD INDEX `hashtag_follows_profile_id_index`(`profile_id`);
ALTER TABLE
    `hashtag_follows` ADD INDEX `hashtag_follows_hashtag_id_index`(`hashtag_id`);
CREATE TABLE `hashtags`(
    `id` BIGINT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `is_nsfw` TINYINT NOT NULL,
    `is_banned` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `hashtags` ADD UNIQUE `hashtags_name_unique`(`name`);
ALTER TABLE
    `hashtags` ADD UNIQUE `hashtags_slug_unique`(`slug`);
CREATE TABLE `import_datas`(
    `id` INT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `job_id` BIGINT NULL,
    `service` VARCHAR(255) NOT NULL,
    `path` VARCHAR(255) NULL,
    `stage` TINYINT NOT NULL,
    `original_name` VARCHAR(255) NULL,
    `import_accepted` TINYINT NULL,
    `completed_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `import_datas` ADD UNIQUE `import_datas_job_id_original_name_unique`(`job_id`, `original_name`);
CREATE TABLE `import_jobs`(
    `id` INT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `service` VARCHAR(255) NOT NULL,
    `uuid` VARCHAR(255) NULL,
    `storage_path` VARCHAR(255) NULL,
    `stage` TINYINT NOT NULL,
    `media_json` TEXT NULL,
    `completed_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `instances`(
    `id` BIGINT NOT NULL,
    `domain` VARCHAR(255) NOT NULL,
    `url` VARCHAR(255) NULL,
    `name` VARCHAR(255) NULL,
    `admin_url` VARCHAR(255) NULL,
    `limit_reason` VARCHAR(255) NULL,
    `unlisted` TINYINT NOT NULL,
    `auto_cw` TINYINT NOT NULL,
    `banned` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `instances` ADD UNIQUE `instances_domain_unique`(`domain`);
CREATE TABLE `jobs`(
    `id` BIGINT NOT NULL,
    `queue` VARCHAR(255) NOT NULL,
    `payload` LONGTEXT NOT NULL,
    `attempts` TINYINT NOT NULL,
    `reserved_at` INT NULL,
    `available_at` INT NOT NULL,
    `created_at` INT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `jobs` ADD INDEX `jobs_queue_index`(`queue`);
CREATE TABLE `likes`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `status_id` BIGINT NOT NULL,
    `flagged` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `likes` ADD UNIQUE `likes_profile_id_status_id_unique`(`profile_id`, `status_id`);
ALTER TABLE
    `likes` ADD INDEX `likes_created_at_index`(`created_at`);
ALTER TABLE
    `likes` ADD INDEX `likes_deleted_at_index`(`deleted_at`);
CREATE TABLE `media`(
    `id` INT NOT NULL,
    `status_id` BIGINT NULL,
    `profile_id` BIGINT NULL,
    `user_id` BIGINT NULL,
    `is_nsfw` TINYINT NOT NULL,
    `remote_media` TINYINT NOT NULL,
    `original_sha256` VARCHAR(255) NULL,
    `optimized_sha256` VARCHAR(255) NULL,
    `media_path` VARCHAR(255) NOT NULL,
    `thumbnail_path` VARCHAR(255) NULL,
    `cdn_url` VARCHAR(255) NULL,
    `optimized_url` VARCHAR(255) NULL,
    `thumbnail_url` VARCHAR(255) NULL,
    `remote_url` VARCHAR(255) NULL,
    `caption` VARCHAR(255) NULL,
    `hls_path` VARCHAR(255) NULL,
    `order` TINYINT NOT NULL,
    `mime` VARCHAR(255) NULL,
    `size` INT NULL,
    `orientation` VARCHAR(255) NULL,
    `filter_name` VARCHAR(255) NULL,
    `filter_class` VARCHAR(255) NULL,
    `license` VARCHAR(255) NULL,
    `processed_at` TIMESTAMP NULL,
    `hls_transcoded_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    `key` VARCHAR(255) NULL,
    `metadata` JSON NULL,
    `version` TINYINT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `media` ADD UNIQUE `media_status_id_media_path_unique`(`status_id`, `media_path`);
ALTER TABLE
    `media` ADD INDEX `media_user_id_index`(`user_id`);
ALTER TABLE
    `media` ADD INDEX `media_original_sha256_index`(`original_sha256`);
ALTER TABLE
    `media` ADD INDEX `media_optimized_sha256_index`(`optimized_sha256`);
ALTER TABLE
    `media` ADD INDEX `media_deleted_at_index`(`deleted_at`);
CREATE TABLE `mentions`(
    `id` BIGINT NOT NULL,
    `status_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `local` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `mentions` ADD INDEX `mentions_deleted_at_index`(`deleted_at`);
CREATE TABLE `migrations`(
    `id` INT NOT NULL,
    `migration` VARCHAR(255) NOT NULL,
    `batch` INT NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `mod_logs`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `user_username` VARCHAR(255) NULL,
    `object_uid` BIGINT NULL,
    `object_id` BIGINT NULL,
    `object_type` VARCHAR(255) NULL,
    `action` VARCHAR(255) NULL,
    `message` TEXT NULL,
    `metadata` JSON NULL,
    `access_level` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `mod_logs` ADD INDEX `mod_logs_user_id_index`(`user_id`);
ALTER TABLE
    `mod_logs` ADD INDEX `mod_logs_object_uid_index`(`object_uid`);
ALTER TABLE
    `mod_logs` ADD INDEX `mod_logs_object_id_index`(`object_id`);
ALTER TABLE
    `mod_logs` ADD INDEX `mod_logs_object_type_index`(`object_type`);
CREATE TABLE `newsroom`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NULL,
    `header_photo_url` VARCHAR(255) NULL,
    `title` VARCHAR(255) NULL,
    `slug` VARCHAR(255) NULL,
    `category` VARCHAR(255) NOT NULL,
    `summary` TEXT NULL,
    `body` TEXT NULL,
    `body_rendered` TEXT NULL,
    `link` VARCHAR(255) NULL,
    `force_modal` TINYINT NOT NULL,
    `show_timeline` TINYINT NOT NULL,
    `show_link` TINYINT NOT NULL,
    `auth_only` TINYINT NOT NULL,
    `published_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `newsroom` ADD UNIQUE `newsroom_slug_unique`(`slug`);
CREATE TABLE `notifications`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `actor_id` BIGINT NULL,
    `item_id` BIGINT NULL,
    `item_type` VARCHAR(255) NULL,
    `action` VARCHAR(255) NULL,
    `message` VARCHAR(255) NULL,
    `rendered` VARCHAR(255) NULL,
    `read_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `notifications` ADD INDEX `notifications_profile_id_index`(`profile_id`);
ALTER TABLE
    `notifications` ADD INDEX `notifications_actor_id_index`(`actor_id`);
ALTER TABLE
    `notifications` ADD INDEX `notifications_created_at_index`(`created_at`);
ALTER TABLE
    `notifications` ADD INDEX `notifications_deleted_at_index`(`deleted_at`);
CREATE TABLE `oauth_access_tokens`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` BIGINT NULL,
    `client_id` INT NOT NULL,
    `name` VARCHAR(255) NULL,
    `scopes` TEXT NULL,
    `revoked` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `expires_at` DATETIME NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `oauth_access_tokens` ADD INDEX `oauth_access_tokens_user_id_index`(`user_id`);
CREATE TABLE `oauth_auth_codes`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` BIGINT NOT NULL,
    `client_id` INT NOT NULL,
    `scopes` TEXT NULL,
    `revoked` TINYINT NOT NULL,
    `expires_at` DATETIME NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `oauth_clients`(
    `id` INT NOT NULL,
    `user_id` BIGINT NULL,
    `name` VARCHAR(255) NOT NULL,
    `secret` VARCHAR(255) NOT NULL,
    `redirect` TEXT NOT NULL,
    `personal_access_client` TINYINT NOT NULL,
    `password_client` TINYINT NOT NULL,
    `revoked` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `oauth_clients` ADD INDEX `oauth_clients_user_id_index`(`user_id`);
CREATE TABLE `oauth_personal_access_clients`(
    `id` INT NOT NULL,
    `client_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `oauth_personal_access_clients` ADD INDEX `oauth_personal_access_clients_client_id_index`(`client_id`);
CREATE TABLE `oauth_refresh_tokens`(
    `id` VARCHAR(255) NOT NULL,
    `access_token_id` VARCHAR(255) NOT NULL,
    `revoked` TINYINT NOT NULL,
    `expires_at` DATETIME NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `oauth_refresh_tokens` ADD INDEX `oauth_refresh_tokens_access_token_id_index`(`access_token_id`);
CREATE TABLE `pages`(
    `id` BIGINT NOT NULL,
    `root` VARCHAR(255) NULL,
    `slug` VARCHAR(255) NULL,
    `title` VARCHAR(255) NULL,
    `category_id` INT NULL,
    `content` LONGTEXT NULL,
    `template` VARCHAR(255) NOT NULL,
    `active` TINYINT NOT NULL,
    `cached` TINYINT NOT NULL,
    `active_until` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `pages` ADD INDEX `pages_root_index`(`root`);
ALTER TABLE
    `pages` ADD UNIQUE `pages_slug_unique`(`slug`);
ALTER TABLE
    `pages` ADD INDEX `pages_category_id_index`(`category_id`);
ALTER TABLE
    `pages` ADD INDEX `pages_template_index`(`template`);
ALTER TABLE
    `pages` ADD INDEX `pages_active_index`(`active`);
ALTER TABLE
    `pages` ADD INDEX `pages_cached_index`(`cached`);
CREATE TABLE `password_resets`(
    `email` VARCHAR(255) NOT NULL,
    `token` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL
);
ALTER TABLE
    `password_resets` ADD INDEX `password_resets_email_index`(`email`);
CREATE TABLE `places`(
    `id` BIGINT NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `country` VARCHAR(255) NOT NULL,
    `aliases` JSON NULL,
    `lat` DECIMAL(8, 2) NULL,
    `long` DECIMAL(8, 2) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `places` ADD UNIQUE `places_slug_country_lat_long_unique`(`slug`, `country`, `lat`, `long`);
ALTER TABLE
    `places` ADD INDEX `places_slug_index`(`slug`);
ALTER TABLE
    `places` ADD INDEX `places_name_index`(`name`);
ALTER TABLE
    `places` ADD INDEX `places_country_index`(`country`);
CREATE TABLE `profile_sponsors`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `sponsors` JSON NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `profile_sponsors` ADD UNIQUE `profile_sponsors_profile_id_unique`(`profile_id`);
CREATE TABLE `profiles`(
    `id` BIGINT NOT NULL,
    `user_id` INT NULL,
    `domain` VARCHAR(255) NULL,
    `username` VARCHAR(255) NULL,
    `status` VARCHAR(255) NULL,
    `name` VARCHAR(255) NULL,
    `bio` TEXT NULL,
    `unlisted` TINYINT NOT NULL,
    `cw` TINYINT NOT NULL,
    `no_autolink` TINYINT NOT NULL,
    `location` VARCHAR(255) NULL,
    `website` VARCHAR(255) NULL,
    `profile_layout` VARCHAR(255) NULL,
    `header_bg` VARCHAR(255) NULL,
    `post_layout` VARCHAR(255) NULL,
    `is_private` TINYINT NOT NULL,
    `sharedInbox` VARCHAR(255) NULL,
    `inbox_url` VARCHAR(255) NULL,
    `outbox_url` VARCHAR(255) NULL,
    `key_id` VARCHAR(255) NULL,
    `follower_url` VARCHAR(255) NULL,
    `following_url` VARCHAR(255) NULL,
    `private_key` TEXT NULL,
    `public_key` TEXT NULL,
    `remote_url` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    `delete_after` TIMESTAMP NULL,
    `is_suggestable` TINYINT NOT NULL,
    `last_fetched_at` TIMESTAMP NULL,
    `status_count` INT NULL,
    `followers_count` INT NULL,
    `following_count` INT NULL,
    `webfinger` VARCHAR(255) NULL,
    `avatar_url` VARCHAR(255) NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `profiles` ADD UNIQUE `profiles_domain_username_unique`(`domain`, `username`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_domain_index`(`domain`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_username_index`(`username`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_status_index`(`status`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_unlisted_index`(`unlisted`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_cw_index`(`cw`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_no_autolink_index`(`no_autolink`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_sharedinbox_index`(`sharedInbox`);
ALTER TABLE
    `profiles` ADD UNIQUE `profiles_key_id_unique`(`key_id`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_deleted_at_index`(`deleted_at`);
ALTER TABLE
    `profiles` ADD INDEX `profiles_is_suggestable_index`(`is_suggestable`);
ALTER TABLE
    `profiles` ADD UNIQUE `profiles_webfinger_unique`(`webfinger`);
CREATE TABLE `report_comments`(
    `id` INT NOT NULL,
    `report_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `comment` TEXT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `report_comments` ADD INDEX `report_comments_report_id_index`(`report_id`);
CREATE TABLE `report_logs`(
    `id` INT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `item_id` BIGINT NULL,
    `item_type` VARCHAR(255) NULL,
    `action` VARCHAR(255) NULL,
    `system_message` TINYINT NOT NULL,
    `metadata` JSON NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `reports`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `user_id` BIGINT NULL,
    `object_id` BIGINT NOT NULL,
    `object_type` VARCHAR(255) NULL,
    `reported_profile_id` BIGINT NULL,
    `type` VARCHAR(255) NULL,
    `message` VARCHAR(255) NULL,
    `admin_seen` TIMESTAMP NULL,
    `not_interested` TINYINT NOT NULL,
    `spam` TINYINT NOT NULL,
    `nsfw` TINYINT NOT NULL,
    `abusive` TINYINT NOT NULL,
    `meta` JSON NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `reports` ADD UNIQUE `reports_user_id_object_id_object_type_unique`(
        `user_id`,
        `object_id`,
        `object_type`
    );
CREATE TABLE `sessions`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` BIGINT NULL,
    `ip_address` VARCHAR(255) NULL,
    `user_agent` TEXT NULL,
    `payload` TEXT NOT NULL,
    `last_activity` INT NOT NULL
);
ALTER TABLE
    `sessions` ADD UNIQUE `sessions_id_unique`(`id`);
CREATE TABLE `status_hashtags`(
    `id` BIGINT NOT NULL,
    `status_id` BIGINT NOT NULL,
    `hashtag_id` BIGINT NOT NULL,
    `profile_id` BIGINT NULL,
    `status_visibility` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `status_hashtags` ADD UNIQUE `status_hashtags_status_id_hashtag_id_unique`(`status_id`, `hashtag_id`);
ALTER TABLE
    `status_hashtags` ADD INDEX `status_hashtags_status_id_index`(`status_id`);
ALTER TABLE
    `status_hashtags` ADD INDEX `status_hashtags_hashtag_id_index`(`hashtag_id`);
ALTER TABLE
    `status_hashtags` ADD INDEX `status_hashtags_profile_id_index`(`profile_id`);
ALTER TABLE
    `status_hashtags` ADD INDEX `status_hashtags_status_visibility_index`(`status_visibility`);
CREATE TABLE `statuses`(
    `id` BIGINT NOT NULL,
    `uri` VARCHAR(255) NULL,
    `caption` TEXT NULL,
    `rendered` TEXT NULL,
    `profile_id` BIGINT NULL,
    `type` VARCHAR(255) NULL,
    `in_reply_to_id` BIGINT NULL,
    `reblog_of_id` BIGINT NULL,
    `url` VARCHAR(255) NULL,
    `is_nsfw` TINYINT NOT NULL,
    `scope` VARCHAR(255) NOT NULL,
    `visibility` ENUM('') NOT NULL,
    `reply` TINYINT NOT NULL,
    `likes_count` BIGINT NOT NULL,
    `reblogs_count` BIGINT NOT NULL,
    `language` VARCHAR(255) NULL,
    `conversation_id` BIGINT NULL,
    `local` TINYINT NOT NULL,
    `application_id` BIGINT NULL,
    `in_reply_to_profile_id` BIGINT NULL,
    `entities` JSON NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    `cw_summary` VARCHAR(255) NULL,
    `reply_count` INT NULL,
    `comments_disabled` TINYINT NOT NULL,
    `place_id` BIGINT NULL,
    `object_url` VARCHAR(255) NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `statuses` ADD INDEX `statuses_in_reply_to_id_reblog_of_id_index`(`in_reply_to_id`, `reblog_of_id`);
ALTER TABLE
    `statuses` ADD UNIQUE `statuses_uri_unique`(`uri`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_profile_id_index`(`profile_id`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_type_index`(`type`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_is_nsfw_index`(`is_nsfw`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_scope_index`(`scope`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_visibility_index`(`visibility`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_local_index`(`local`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_created_at_index`(`created_at`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_deleted_at_index`(`deleted_at`);
ALTER TABLE
    `statuses` ADD INDEX `statuses_place_id_index`(`place_id`);
ALTER TABLE
    `statuses` ADD UNIQUE `statuses_object_url_unique`(`object_url`);
CREATE TABLE `stories`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `type` VARCHAR(255) NULL,
    `size` INT NULL,
    `mime` VARCHAR(255) NULL,
    `duration` SMALLINT NOT NULL,
    `path` VARCHAR(255) NULL,
    `cdn_url` VARCHAR(255) NULL,
    `public` TINYINT NOT NULL,
    `local` TINYINT NOT NULL,
    `view_count` INT NULL,
    `comment_count` INT NULL,
    `story` JSON NULL,
    `expires_at` TIMESTAMP NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `stories` ADD UNIQUE `stories_profile_id_path_unique`(`profile_id`, `path`);
ALTER TABLE
    `stories` ADD INDEX `stories_profile_id_index`(`profile_id`);
ALTER TABLE
    `stories` ADD INDEX `stories_public_index`(`public`);
ALTER TABLE
    `stories` ADD INDEX `stories_local_index`(`local`);
ALTER TABLE
    `stories` ADD INDEX `stories_expires_at_index`(`expires_at`);
CREATE TABLE `story_views`(
    `id` BIGINT NOT NULL,
    `story_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `story_views` ADD UNIQUE `story_views_story_id_profile_id_unique`(`story_id`, `profile_id`);
ALTER TABLE
    `story_views` ADD INDEX `story_views_story_id_index`(`story_id`);
ALTER TABLE
    `story_views` ADD INDEX `story_views_profile_id_index`(`profile_id`);
CREATE TABLE `user_devices`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `ip` VARCHAR(255) NOT NULL,
    `user_agent` VARCHAR(255) NOT NULL,
    `fingerprint` VARCHAR(255) NULL,
    `name` VARCHAR(255) NULL,
    `trusted` TINYINT NULL,
    `last_active_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `user_devices` ADD UNIQUE `user_devices_user_id_ip_user_agent_fingerprint_unique`(
        `user_id`,
        `ip`,
        `user_agent`,
        `fingerprint`
    );
ALTER TABLE
    `user_devices` ADD INDEX `user_devices_user_id_index`(`user_id`);
ALTER TABLE
    `user_devices` ADD INDEX `user_devices_ip_index`(`ip`);
ALTER TABLE
    `user_devices` ADD INDEX `user_devices_user_agent_index`(`user_agent`);
CREATE TABLE `user_filters`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `filterable_id` BIGINT NOT NULL,
    `filterable_type` VARCHAR(255) NOT NULL,
    `filter_type` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `user_filters` ADD UNIQUE `user_id_filterable_id_filterable_type_filter_type_unique`(
        `user_id`,
        `filterable_id`,
        `filterable_type`,
        `filter_type`
    );
ALTER TABLE
    `user_filters` ADD INDEX `user_filters_user_id_index`(`user_id`);
ALTER TABLE
    `user_filters` ADD INDEX `user_filters_filter_type_index`(`filter_type`);
CREATE TABLE `user_invites`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `profile_id` BIGINT NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `message` TEXT NULL,
    `key` VARCHAR(255) NOT NULL,
    `token` VARCHAR(255) NOT NULL,
    `valid_until` TIMESTAMP NULL,
    `used_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `user_invites` ADD INDEX `user_invites_user_id_index`(`user_id`);
ALTER TABLE
    `user_invites` ADD INDEX `user_invites_profile_id_index`(`profile_id`);
ALTER TABLE
    `user_invites` ADD UNIQUE `user_invites_email_unique`(`email`);
ALTER TABLE
    `user_invites` ADD INDEX `user_invites_used_at_index`(`used_at`);
CREATE TABLE `user_settings`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `role` VARCHAR(255) NOT NULL,
    `crawlable` TINYINT NOT NULL,
    `show_guests` TINYINT NOT NULL,
    `show_discover` TINYINT NOT NULL,
    `public_dm` TINYINT NOT NULL,
    `hide_cw_search` TINYINT NOT NULL,
    `hide_blocked_search` TINYINT NOT NULL,
    `always_show_cw` TINYINT NOT NULL,
    `compose_media_descriptions` TINYINT NOT NULL,
    `reduce_motion` TINYINT NOT NULL,
    `optimize_screen_reader` TINYINT NOT NULL,
    `high_contrast_mode` TINYINT NOT NULL,
    `video_autoplay` TINYINT NOT NULL,
    `send_email_new_follower` TINYINT NOT NULL,
    `send_email_new_follower_request` TINYINT NOT NULL,
    `send_email_on_share` TINYINT NOT NULL,
    `send_email_on_like` TINYINT NOT NULL,
    `send_email_on_mention` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `show_profile_followers` TINYINT NOT NULL,
    `show_profile_follower_count` TINYINT NOT NULL,
    `show_profile_following` TINYINT NOT NULL,
    `show_profile_following_count` TINYINT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `user_settings` ADD UNIQUE `user_settings_user_id_unique`(`user_id`);
CREATE TABLE `users`(
    `id` BIGINT NOT NULL,
    `profile_id` BIGINT NULL,
    `name` VARCHAR(255) NULL,
    `username` VARCHAR(255) NULL,
    `email` VARCHAR(255) NOT NULL,
    `status` VARCHAR(255) NULL,
    `language` VARCHAR(255) NULL,
    `password` VARCHAR(255) NOT NULL,
    `remember_token` VARCHAR(255) NULL,
    `is_admin` TINYINT NOT NULL,
    `email_verified_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    `2fa_enabled` TINYINT NOT NULL,
    `2fa_secret` VARCHAR(255) NULL,
    `2fa_backup_codes` JSON NULL,
    `2fa_setup_at` TIMESTAMP NULL,
    `delete_after` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `users` ADD UNIQUE `users_profile_id_unique`(`profile_id`);
ALTER TABLE
    `users` ADD UNIQUE `users_username_unique`(`username`);
ALTER TABLE
    `users` ADD UNIQUE `users_email_unique`(`email`);
ALTER TABLE
    `users` ADD INDEX `users_status_index`(`status`);
ALTER TABLE
    `users` ADD INDEX `users_language_index`(`language`);
ALTER TABLE
    `users` ADD INDEX `users_deleted_at_index`(`deleted_at`);
CREATE TABLE `websockets_statistics_entries`(
    `id` INT NOT NULL,
    `app_id` VARCHAR(255) NOT NULL,
    `peak_connection_count` INT NOT NULL,
    `websocket_message_count` INT NOT NULL,
    `api_message_count` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `direct_messages` ADD CONSTRAINT `direct_messages_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `user_filters` ADD CONSTRAINT `user_filters_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `hashtag_follows` ADD CONSTRAINT `hashtag_follows_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `notifications` ADD CONSTRAINT `notifications_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `story_views` ADD CONSTRAINT `story_views_story_id_foreign` FOREIGN KEY(`story_id`) REFERENCES `stories`(`id`);
ALTER TABLE
    `oauth_clients` ADD CONSTRAINT `oauth_clients_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `bookmarks` ADD CONSTRAINT `bookmarks_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `report_comments` ADD CONSTRAINT `report_comments_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `report_comments` ADD CONSTRAINT `report_comments_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `report_logs` ADD CONSTRAINT `report_logs_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `reports` ADD CONSTRAINT `reports_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `followers` ADD CONSTRAINT `followers_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `mentions` ADD CONSTRAINT `mentions_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `statuses` ADD CONSTRAINT `statuses_place_id_foreign` FOREIGN KEY(`place_id`) REFERENCES `places`(`id`);
ALTER TABLE
    `statuses` ADD CONSTRAINT `statuses_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `comments` ADD CONSTRAINT `comments_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `mod_logs` ADD CONSTRAINT `mod_logs_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `collections` ADD CONSTRAINT `collections_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `import_datas` ADD CONSTRAINT `import_datas_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `likes` ADD CONSTRAINT `likes_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `hashtag_follows` ADD CONSTRAINT `hashtag_follows_hashtag_id_foreign` FOREIGN KEY(`hashtag_id`) REFERENCES `hashtags`(`id`);
ALTER TABLE
    `circle_profiles` ADD CONSTRAINT `circle_profiles_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `report_comments` ADD CONSTRAINT `report_comments_report_id_foreign` FOREIGN KEY(`report_id`) REFERENCES `reports`(`id`);
ALTER TABLE
    `newsroom` ADD CONSTRAINT `newsroom_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `profiles` ADD CONSTRAINT `profiles_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `circles` ADD CONSTRAINT `circles_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `status_hashtags` ADD CONSTRAINT `status_hashtags_hashtag_id_foreign` FOREIGN KEY(`hashtag_id`) REFERENCES `hashtags`(`id`);
ALTER TABLE
    `discover_category_hashtags` ADD CONSTRAINT `discover_category_hashtags_hashtag_id_foreign` FOREIGN KEY(`hashtag_id`) REFERENCES `hashtags`(`id`);
ALTER TABLE
    `discover_category_hashtags` ADD CONSTRAINT `discover_category_hashtags_discover_category_id_foreign` FOREIGN KEY(`discover_category_id`) REFERENCES `discover_categories`(`id`);
ALTER TABLE
    `hashtag_follows` ADD CONSTRAINT `hashtag_follows_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `status_hashtags` ADD CONSTRAINT `status_hashtags_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `comments` ADD CONSTRAINT `comments_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `account_logs` ADD CONSTRAINT `account_logs_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `import_datas` ADD CONSTRAINT `import_datas_job_id_foreign` FOREIGN KEY(`job_id`) REFERENCES `jobs`(`id`);
ALTER TABLE
    `profile_sponsors` ADD CONSTRAINT `profile_sponsors_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `user_invites` ADD CONSTRAINT `user_invites_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `circle_profiles` ADD CONSTRAINT `circle_profiles_circle_id_foreign` FOREIGN KEY(`circle_id`) REFERENCES `circles`(`id`);
ALTER TABLE
    `follow_requests` ADD CONSTRAINT `follow_requests_follower_id_foreign` FOREIGN KEY(`follower_id`) REFERENCES `followers`(`id`);
ALTER TABLE
    `discover_categories` ADD CONSTRAINT `discover_categories_media_id_foreign` FOREIGN KEY(`media_id`) REFERENCES `media`(`id`);
ALTER TABLE
    `status_hashtags` ADD CONSTRAINT `status_hashtags_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `user_invites` ADD CONSTRAINT `user_invites_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `email_verifications` ADD CONSTRAINT `email_verifications_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `media` ADD CONSTRAINT `media_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `oauth_refresh_tokens` ADD CONSTRAINT `oauth_refresh_tokens_access_token_id_foreign` FOREIGN KEY(`access_token_id`) REFERENCES `oauth_access_tokens`(`id`);
ALTER TABLE
    `user_devices` ADD CONSTRAINT `user_devices_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `bookmarks` ADD CONSTRAINT `bookmarks_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `oauth_access_tokens` ADD CONSTRAINT `oauth_access_tokens_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `sessions` ADD CONSTRAINT `sessions_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `media` ADD CONSTRAINT `media_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `stories` ADD CONSTRAINT `stories_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `oauth_auth_codes` ADD CONSTRAINT `oauth_auth_codes_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `story_views` ADD CONSTRAINT `story_views_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `mentions` ADD CONSTRAINT `mentions_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `comments` ADD CONSTRAINT `comments_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `collection_items` ADD CONSTRAINT `collection_items_collection_id_foreign` FOREIGN KEY(`collection_id`) REFERENCES `collections`(`id`);
ALTER TABLE
    `import_jobs` ADD CONSTRAINT `import_jobs_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `reports` ADD CONSTRAINT `reports_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `user_settings` ADD CONSTRAINT `user_settings_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `likes` ADD CONSTRAINT `likes_status_id_foreign` FOREIGN KEY(`status_id`) REFERENCES `statuses`(`id`);
ALTER TABLE
    `media` ADD CONSTRAINT `media_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);
ALTER TABLE
    `contacts` ADD CONSTRAINT `contacts_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `avatars` ADD CONSTRAINT `avatars_profile_id_foreign` FOREIGN KEY(`profile_id`) REFERENCES `profiles`(`id`);