-- Reference design only. The executable JSONL engagement galaxy is documented in
-- docs/modeling/egypt-engagement-implementation.md and built by src/build_analytics.py.
-- This file does not create/migrate the saved Power BI semantic model.

-- ============================================================================
-- PixelFed Analytics Engineering - Gold Layer Dimensional Galaxy Schema DDL
-- Kimball Dimensional Modeling Specification for Data Warehousing & Analytics
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Conformed Dimension: dim_date
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT NOT NULL,                  -- Format: YYYYMMDD
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    quarter_name VARCHAR(10) NOT NULL,      -- e.g. 'Q1 2026'
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,        -- e.g. 'January'
    month_year VARCHAR(10) NOT NULL,        -- e.g. 'Jan 2026'
    week_of_year INT NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,               -- 1 (Monday) - 7 (Sunday)
    day_name VARCHAR(20) NOT NULL,          -- e.g. 'Monday'
    is_weekend BOOLEAN NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL,
    PRIMARY KEY (date_key)
);

-- ----------------------------------------------------------------------------
-- Conformed Dimension: dim_instances (Fediverse Servers)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_instances (
    instance_key BIGINT NOT NULL,           -- Surrogate Key or Source ID
    instance_id BIGINT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    title VARCHAR(255) NULL,
    description TEXT NULL,
    is_local BOOLEAN NOT NULL,
    is_blocked BOOLEAN NOT NULL,
    software VARCHAR(100) NULL,
    version VARCHAR(50) NULL,
    created_at TIMESTAMP NULL,
    PRIMARY KEY (instance_key)
);

-- ----------------------------------------------------------------------------
-- Conformed Dimension: dim_users (Authentication & Account Layer)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_users (
    user_key BIGINT NOT NULL,               -- Surrogate Key
    user_id BIGINT NOT NULL,
    email_domain VARCHAR(255) NULL,         -- Masked domain for analytics (synthetic)
    is_admin BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    has_2fa BOOLEAN NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_date_key INT NOT NULL,
    created_at TIMESTAMP NULL,
    PRIMARY KEY (user_key)
);

-- ----------------------------------------------------------------------------
-- Conformed Dimension: dim_profiles (Public Federation Personas)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_profiles (
    profile_key BIGINT NOT NULL,            -- Surrogate Key
    profile_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    instance_id BIGINT NULL,
    username VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NULL,
    is_local BOOLEAN NOT NULL,
    is_private BOOLEAN NOT NULL,
    is_verified BOOLEAN NOT NULL,
    is_curated BOOLEAN NOT NULL,
    created_date_key INT NOT NULL,
    created_at TIMESTAMP NULL,
    PRIMARY KEY (profile_key)
);

-- ----------------------------------------------------------------------------
-- Conformed Dimension: dim_hashtags
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_hashtags (
    hashtag_key BIGINT NOT NULL,
    hashtag_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    is_featured BOOLEAN NOT NULL,
    created_at TIMESTAMP NULL,
    PRIMARY KEY (hashtag_key)
);

-- ----------------------------------------------------------------------------
-- Fact Table: fct_posts (Granularity: 1 row per status / publication)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fct_posts (
    post_key BIGINT NOT NULL,
    status_id BIGINT NOT NULL,
    profile_key BIGINT NOT NULL,
    created_date_key INT NOT NULL,
    scope VARCHAR(50) NOT NULL,             -- 'public', 'unlisted', 'private', 'direct'
    type VARCHAR(50) NOT NULL,              -- 'photo', 'video', 'album', 'status'
    has_media BOOLEAN NOT NULL,
    is_nsfw BOOLEAN NOT NULL,
    media_count INT NOT NULL DEFAULT 0,
    character_length INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (post_key),
    FOREIGN KEY (profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (created_date_key) REFERENCES dim_date(date_key)
);

-- ----------------------------------------------------------------------------
-- Fact Table: fct_likes (Granularity: 1 row per like event)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fct_likes (
    like_key BIGINT NOT NULL,
    like_id BIGINT NOT NULL,
    profile_key BIGINT NOT NULL,            -- Profile who liked
    status_key BIGINT NOT NULL,             -- Status being liked
    author_profile_key BIGINT NOT NULL,     -- Author of the status
    like_date_key INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (like_key),
    FOREIGN KEY (profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (status_key) REFERENCES fct_posts(post_key),
    FOREIGN KEY (like_date_key) REFERENCES dim_date(date_key)
);

-- ----------------------------------------------------------------------------
-- Fact Table: fct_comments (Granularity: 1 row per comment)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fct_comments (
    comment_key BIGINT NOT NULL,
    comment_id BIGINT NOT NULL,
    profile_key BIGINT NOT NULL,
    status_key BIGINT NOT NULL,
    author_profile_key BIGINT NOT NULL,
    comment_date_key INT NOT NULL,
    character_length INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (comment_key),
    FOREIGN KEY (profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (status_key) REFERENCES fct_posts(post_key),
    FOREIGN KEY (comment_date_key) REFERENCES dim_date(date_key)
);

-- ----------------------------------------------------------------------------
-- Fact Table: fct_follows (Granularity: 1 row per follow edge)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fct_follows (
    follow_key BIGINT NOT NULL,
    follow_id BIGINT NOT NULL,
    follower_profile_key BIGINT NOT NULL,
    following_profile_key BIGINT NOT NULL,
    follow_date_key INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (follow_key),
    FOREIGN KEY (follower_profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (following_profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (follow_date_key) REFERENCES dim_date(date_key)
);

-- ----------------------------------------------------------------------------
-- Fact Table: fct_media (Granularity: 1 row per media asset uploaded)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fct_media (
    media_key BIGINT NOT NULL,
    media_id BIGINT NOT NULL,
    profile_key BIGINT NOT NULL,
    status_key BIGINT NULL,
    upload_date_key INT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    width INT NULL,
    height INT NULL,
    orientation VARCHAR(20) NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (media_key),
    FOREIGN KEY (profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (upload_date_key) REFERENCES dim_date(date_key)
);

-- ----------------------------------------------------------------------------
-- Fact Table: fct_story_views (Granularity: 1 row per story impression)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fct_story_views (
    view_key BIGINT NOT NULL,
    view_id BIGINT NOT NULL,
    story_id BIGINT NOT NULL,
    viewer_profile_key BIGINT NOT NULL,
    view_date_key INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (view_key),
    FOREIGN KEY (viewer_profile_key) REFERENCES dim_profiles(profile_key),
    FOREIGN KEY (view_date_key) REFERENCES dim_date(date_key)
);
