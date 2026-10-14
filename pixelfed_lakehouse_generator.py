#!/usr/bin/env python3
"""Generate deterministic synthetic PixelFed data for a multi-format lakehouse.

The output is synthetic training/demo data, not a production PixelFed database dump.
Timestamps are stored as naive UTC values in tabular files; JSONL timestamps are ISO
formatted. The SQLite snapshot stores timestamps as ISO text and enforces selected
primary-key, uniqueness, and foreign-key constraints.

Install dependencies:
    python -m pip install -r requirements.txt

Run the default dataset:
    python pixelfed_lakehouse_generator.py

Run a smaller test dataset:
    python pixelfed_lakehouse_generator.py --scale 0.01 --output-dir ./pixelfed_test
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sqlite3
import sys
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from faker import Faker

LOGGER = logging.getLogger("pixelfed_lakehouse")


@dataclass(frozen=True)
class GeneratorConfig:
    """Row counts and output settings for one reproducible generation run."""

    seed: int = 42
    output_dir: Path = Path("pixelfed_lakehouse_landing")
    as_of: datetime | None = None
    num_users: int = 5_000
    num_statuses: int = 40_000
    num_media: int = 50_000
    num_comments: int = 80_000
    num_likes: int = 200_000
    num_follows: int = 30_000
    num_hashtags: int = 1_000
    num_logs: int = 60_000
    num_activities: int = 50_000
    num_notifications: int = 70_000
    num_messages: int = 25_000

    @property
    def count_fields(self) -> tuple[str, ...]:
        return (
            "num_users",
            "num_statuses",
            "num_media",
            "num_comments",
            "num_likes",
            "num_follows",
            "num_hashtags",
            "num_logs",
            "num_activities",
            "num_notifications",
            "num_messages",
        )

    def validate(self) -> None:
        for field in self.count_fields:
            value = getattr(self, field)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field} must be a non-negative integer; received {value!r}.")
        if self.as_of is not None:
            as_of = self.as_of
            if as_of.tzinfo is not None:
                as_of = as_of.astimezone(timezone.utc).replace(tzinfo=None)
            if as_of <= datetime(2022, 2, 1):
                raise ValueError("as_of must be later than 2022-02-01 to support the generated date ranges.")

        profile_dependent = (
            self.num_statuses
            + self.num_media
            + self.num_comments
            + self.num_likes
            + self.num_follows
            + self.num_activities
            + self.num_notifications
            + self.num_messages
            + self.num_logs
        )
        if profile_dependent and self.num_users == 0:
            raise ValueError("Users/profiles are required when profile-dependent datasets are requested.")
        if self.num_media and not self.num_statuses:
            raise ValueError("num_media must be 0 when num_statuses is 0.")
        if (self.num_comments or self.num_likes) and not self.num_statuses:
            raise ValueError("Comments and likes require at least one status.")
        if self.num_notifications and not any(
            (self.num_statuses, self.num_likes, self.num_comments, self.num_follows)
        ):
            raise ValueError(
                "Notifications need at least one available status, like, comment, or follow item to reference."
            )

        profile_count = self.num_users
        like_capacity = profile_count * self.num_statuses
        follow_capacity = profile_count * max(0, profile_count - 1)
        if self.num_likes > like_capacity:
            raise ValueError(
                f"num_likes={self.num_likes:,} exceeds the unique profile/status pair capacity "
                f"({like_capacity:,})."
            )
        if self.num_follows > follow_capacity:
            raise ValueError(
                f"num_follows={self.num_follows:,} exceeds the unique non-self follow capacity "
                f"({follow_capacity:,})."
            )


def _latest_dates(*date_series: Iterable[Any]) -> pd.Series:
    """Element-wise maximum of one or more datetime series."""
    if not date_series:
        return pd.Series(dtype="datetime64[ns]")
    converted = [pd.to_datetime(pd.Series(values).reset_index(drop=True)) for values in date_series]
    if not converted:
        return pd.Series(dtype="datetime64[ns]")
    arrays = [values.to_numpy(dtype="datetime64[ns]") for values in converted]
    latest = np.maximum.reduce(arrays)
    return pd.Series(pd.to_datetime(latest))


class PixelFedLakehouseGenerator:
    """Generate, validate, and export synthetic PixelFed-style datasets."""


    # Data lake layout: dimensions/snapshots, analytics-friendly facts, and event streams.
    EXPORT_GROUPS: dict[str, tuple[str, ...]] = {
        "batch_csv_gz": ("users", "profiles", "hashtags"),
        "columnar_parquet": ("statuses", "media", "likes", "comments", "followers"),
        "streaming_jsonl": ("account_logs", "activities", "notifications"),
        "binary_feather": ("direct_messages",),
    }

    SQLITE_ORDER = (
        "users",
        "profiles",
        "statuses",
        "media",
        "likes",
        "comments",
        "followers",
        "hashtags",
        "account_logs",
        "activities",
        "notifications",
        "direct_messages",
    )

    # Child columns mapped to a parent table and key for SQLite foreign keys.
    SQLITE_FOREIGN_KEYS: dict[str, tuple[tuple[str, str, str], ...]] = {
        "profiles": (("user_id", "users", "id"),),
        "statuses": (("profile_id", "profiles", "id"),),
        "media": (
            ("status_id", "statuses", "id"),
            ("profile_id", "profiles", "id"),
            ("user_id", "users", "id"),
        ),
        "likes": (("profile_id", "profiles", "id"), ("status_id", "statuses", "id")),
        "comments": (
            ("profile_id", "profiles", "id"),
            ("user_id", "users", "id"),
            ("status_id", "statuses", "id"),
        ),
        "followers": (("profile_id", "profiles", "id"), ("following_id", "profiles", "id")),
        "account_logs": (("user_id", "users", "id"),),
        "activities": (("to_id", "profiles", "id"), ("from_id", "profiles", "id")),
        "notifications": (("profile_id", "profiles", "id"), ("actor_id", "profiles", "id")),
        "direct_messages": (("to_id", "profiles", "id"), ("from_id", "profiles", "id"), ("status_id", "statuses", "id")),
    }

    def __init__(self, config: GeneratorConfig) -> None:
        config.validate()
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.py_rng = random.Random(config.seed)
        self.fake = Faker()
        self.fake.seed_instance(config.seed)
        self.generated_at = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        as_of = config.as_of or self.generated_at
        if as_of.tzinfo is not None:
            as_of = as_of.astimezone(timezone.utc).replace(tzinfo=None)
        self.run_at = as_of.replace(microsecond=0)

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------
    def random_dates(self, start: datetime, end: datetime, count: int) -> pd.Series:
        """Generate UTC-naive timestamps uniformly in [start, end)."""
        if count == 0:
            return pd.Series(dtype="datetime64[ns]")
        start_ts = pd.Timestamp(start).value
        end_ts = pd.Timestamp(end).value
        if end_ts <= start_ts:
            raise ValueError(f"Date range must be increasing; received {start!r} to {end!r}.")
        random_ns = self.rng.integers(start_ts, end_ts, size=count, dtype=np.int64)
        return pd.Series(pd.to_datetime(random_ns))

    def add_time_offset(self, base_dates: Iterable[Any], max_days: int = 180) -> pd.Series:
        """Add a non-negative offset, never returning a timestamp after this run's time."""
        bases = pd.to_datetime(pd.Series(base_dates).reset_index(drop=True))
        count = len(bases)
        if count == 0:
            return pd.Series(dtype="datetime64[ns]")
        if max_days < 0:
            raise ValueError("max_days must be non-negative.")
        max_seconds = max_days * 86_400
        if max_seconds:
            seconds = self.rng.integers(0, max_seconds + 1, size=count, dtype=np.int64)
            offsets = pd.to_timedelta(seconds, unit="s")
        else:
            offsets = pd.to_timedelta(np.zeros(count, dtype=np.int64), unit="s")
        return (bases + offsets).clip(upper=pd.Timestamp(self.run_at))

    def _make_ids(self, count: int, *, dtype: Any = np.int64) -> np.ndarray:
        return np.arange(1, count + 1, dtype=dtype)

    def _unique_pairs(
        self,
        left_ids: np.ndarray,
        right_ids: np.ndarray,
        count: int,
        *,
        forbid_self: bool = False,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Sample an exact number of unique pairs without replacement.

        Rejection sampling operates on flattened integer pair keys. It avoids the
        under-counting caused by drawing a fixed sample then dropping duplicates.
        """
        if count == 0:
            empty = np.array([], dtype=np.int64)
            return empty, empty.copy()
        if len(left_ids) == 0 or len(right_ids) == 0:
            raise ValueError("Cannot sample pairs from an empty ID collection.")
        capacity = len(left_ids) * len(right_ids)
        if forbid_self and np.array_equal(left_ids, right_ids):
            capacity -= len(left_ids)
        if count > capacity:
            raise ValueError(f"Requested {count:,} pairs but only {capacity:,} unique pairs are possible.")

        right_size = len(right_ids)
        chosen: list[int] = []
        seen: set[int] = set()
        while len(chosen) < count:
            remaining = count - len(chosen)
            candidates = self.rng.integers(
                0,
                len(left_ids) * right_size,
                size=max(1_024, int(remaining * 1.25)),
                dtype=np.int64,
            )
            for raw_key in candidates:
                key = int(raw_key)
                if key in seen:
                    continue
                left_index, right_index = divmod(key, right_size)
                if forbid_self and left_ids[left_index] == right_ids[right_index]:
                    continue
                seen.add(key)
                chosen.append(key)
                if len(chosen) == count:
                    break

        keys = np.asarray(chosen, dtype=np.int64)
        left_positions = keys // right_size
        right_positions = keys % right_size
        return left_ids[left_positions], right_ids[right_positions]

    def _polymorphic_items(
        self, count: int, candidates_by_type: dict[str, np.ndarray]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Build valid (entity_type, entity_id) values for polymorphic references."""
        available = [(name, ids) for name, ids in candidates_by_type.items() if len(ids)]
        if count == 0:
            return np.array([], dtype=object), np.array([], dtype=np.int64)
        if not available:
            raise ValueError("Cannot build polymorphic references without available entity IDs.")

        type_names = np.asarray([name for name, _ in available], dtype=object)
        selected_types = self.rng.choice(type_names, size=count)
        item_ids = np.empty(count, dtype=np.int64)
        for name, ids in available:
            mask = selected_types == name
            if mask.any():
                item_ids[mask] = self.rng.choice(ids, size=int(mask.sum()))
        return selected_types, item_ids

    # ------------------------------------------------------------------
    # Source-like and dimensional datasets
    # ------------------------------------------------------------------
    def generate_users_and_profiles(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        count = self.config.num_users
        LOGGER.info("Generating users and profiles: %s rows each", f"{count:,}")
        created_at = self.random_dates(
            datetime(2022, 1, 1), self.run_at - timedelta(days=30), count
        )
        updated_at = self.add_time_offset(created_at, max_days=30)

        names = [self.fake.name() for _ in range(count)]
        usernames = [self.fake.unique.user_name() for _ in range(count)]
        emails = [self.fake.unique.email() for _ in range(count)]
        email_verified_at = updated_at.copy()
        if count:
            email_verified_at.loc[self.rng.random(count) < 0.10] = pd.NaT

        users = pd.DataFrame(
            {
                "id": self._make_ids(count),
                "profile_id": self._make_ids(count),
                "name": names,
                "username": usernames,
                "email": emails,
                "status": self.rng.choice(["active", "suspended", "pending"], count, p=[0.92, 0.03, 0.05]),
                "language": "en",
                # Deliberately synthetic placeholders; these are not valid credentials.
                "password": [self.fake.sha256() for _ in range(count)],
                "remember_token": [self.fake.md5() if self.py_rng.random() > 0.5 else None for _ in range(count)],
                "is_admin": self.rng.choice([0, 1], count, p=[0.99, 0.01]).astype(np.int8),
                "email_verified_at": email_verified_at,
                "created_at": created_at,
                "updated_at": updated_at,
                "deleted_at": None,
                "2fa_enabled": self.rng.choice([0, 1], count, p=[0.8, 0.2]).astype(np.int8),
                "2fa_secret": None,
                "2fa_backup_codes": None,
                "2fa_setup_at": None,
                "delete_after": None,
            }
        )

        profiles = pd.DataFrame(
            {
                "id": self._make_ids(count),
                "user_id": self._make_ids(count),
                "domain": None,
                "username": usernames,
                "status": users["status"],
                "name": names,
                "bio": [self.fake.text(max_nb_chars=140) if self.py_rng.random() > 0.2 else None for _ in range(count)],
                "unlisted": self.rng.choice([0, 1], count, p=[0.95, 0.05]).astype(np.int8),
                "cw": np.zeros(count, dtype=np.int8),
                "no_autolink": np.zeros(count, dtype=np.int8),
                "location": [self.fake.city() if self.py_rng.random() > 0.4 else None for _ in range(count)],
                "website": [self.fake.url() if self.py_rng.random() > 0.7 else None for _ in range(count)],
                "profile_layout": "default",
                "header_bg": None,
                "post_layout": "default",
                "is_private": self.rng.choice([0, 1], count, p=[0.85, 0.15]).astype(np.int8),
                "sharedInbox": None,
                "inbox_url": [f"https://pixelfed.social/users/{u}/inbox" for u in usernames],
                "outbox_url": [f"https://pixelfed.social/users/{u}/outbox" for u in usernames],
                "key_id": [f"https://pixelfed.social/users/{u}#main-key" for u in usernames],
                "follower_url": [f"https://pixelfed.social/users/{u}/followers" for u in usernames],
                "following_url": [f"https://pixelfed.social/users/{u}/following" for u in usernames],
                "private_key": None,
                "public_key": None,
                "remote_url": None,
                "created_at": created_at,
                "updated_at": updated_at,
                "deleted_at": None,
                "delete_after": None,
                "is_suggestable": np.ones(count, dtype=np.int8),
                "last_fetched_at": None,
                "status_count": self.rng.integers(0, 150, count),
                "followers_count": self.rng.integers(0, 5_000, count),
                "following_count": self.rng.integers(0, 800, count),
                "webfinger": [f"@{u}@pixelfed.social" for u in usernames],
                "avatar_url": [f"https://pixelfed.social/storage/avatars/{u}.jpg" for u in usernames],
            }
        )
        return users, profiles

    def generate_statuses_and_media(
        self, profiles: pd.DataFrame, users: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        status_count = self.config.num_statuses
        media_count = self.config.num_media
        LOGGER.info("Generating statuses: %s rows; media: %s rows", f"{status_count:,}", f"{media_count:,}")
        profile_ids = profiles["id"].to_numpy(dtype=np.int64)
        assigned_profiles = self.rng.choice(profile_ids, size=status_count) if status_count else np.array([], dtype=np.int64)
        profiles_by_id = profiles.set_index("id")
        profile_created = profiles_by_id.loc[assigned_profiles, "created_at"].reset_index(drop=True)
        created_at = self.add_time_offset(profile_created, max_days=365)
        captions = [self.fake.sentence(nb_words=12) if self.py_rng.random() > 0.15 else None for _ in range(status_count)]
        uris = [
            f"https://pixelfed.social/p/{profile_id}/{uuid.uuid5(uuid.NAMESPACE_URL, f'{self.config.seed}:{idx}:{profile_id}').hex[:10]}"
            for idx, profile_id in enumerate(assigned_profiles, start=1)
        ]

        statuses = pd.DataFrame(
            {
                "id": self._make_ids(status_count),
                "uri": uris,
                "caption": captions,
                "rendered": captions,
                "profile_id": assigned_profiles,
                "type": self.rng.choice(["photo", "video"], status_count, p=[0.85, 0.15]),
                "in_reply_to_id": None,
                "reblog_of_id": None,
                "url": uris,
                "is_nsfw": self.rng.choice([0, 1], status_count, p=[0.97, 0.03]).astype(np.int8),
                "scope": "public",
                "visibility": self.rng.choice(["public", "unlisted", "private"], status_count, p=[0.85, 0.05, 0.10]),
                "reply": np.zeros(status_count, dtype=np.int8),
                "likes_count": self.rng.integers(0, 300, status_count),
                "reblogs_count": self.rng.integers(0, 50, status_count),
                "language": "en",
                "conversation_id": self._make_ids(status_count),
                "local": np.ones(status_count, dtype=np.int8),
                "application_id": None,
                "in_reply_to_profile_id": None,
                "entities": None,
                "created_at": created_at,
                "updated_at": created_at,
                "deleted_at": None,
                "cw_summary": None,
                "reply_count": self.rng.integers(0, 40, status_count),
                "comments_disabled": np.zeros(status_count, dtype=np.int8),
                "place_id": None,
                "object_url": None,
            }
        )

        status_ids = statuses["id"].to_numpy(dtype=np.int64)
        assigned_status_ids = self.rng.choice(status_ids, size=media_count) if media_count else np.array([], dtype=np.int64)
        statuses_by_id = statuses.set_index("id")
        assigned_statuses = statuses_by_id.loc[assigned_status_ids].reset_index(drop=True)
        media_profile_ids = assigned_statuses["profile_id"].to_numpy(dtype=np.int64)
        profile_to_user = profiles.set_index("id")["user_id"]
        media_user_ids = profile_to_user.loc[media_profile_ids].to_numpy(dtype=np.int64)
        media_status_created = assigned_statuses["created_at"].reset_index(drop=True)

        media = pd.DataFrame(
            {
                "id": self._make_ids(media_count),
                "status_id": assigned_status_ids,
                "profile_id": media_profile_ids,
                "user_id": media_user_ids,
                "is_nsfw": np.zeros(media_count, dtype=np.int8),
                "remote_media": np.zeros(media_count, dtype=np.int8),
                "original_sha256": [self.fake.sha256() for _ in range(media_count)],
                "optimized_sha256": [self.fake.sha256() for _ in range(media_count)],
                "media_path": [f"storage/m/{pid}/{sid}_{idx}.jpg" for idx, (pid, sid) in enumerate(zip(media_profile_ids, assigned_status_ids), start=1)],
                "thumbnail_path": [f"storage/m/{pid}/thumb_{sid}_{idx}.jpg" for idx, (pid, sid) in enumerate(zip(media_profile_ids, assigned_status_ids), start=1)],
                "cdn_url": [f"https://cdn.pixelfed.social/m/{sid}.jpg" for sid in assigned_status_ids],
                "optimized_url": None,
                "thumbnail_url": None,
                "remote_url": None,
                "caption": [self.fake.word() for _ in range(media_count)],
                "hls_path": None,
                "order": np.zeros(media_count, dtype=np.int8),
                "mime": np.where(assigned_statuses["type"].to_numpy() == "video", "video/mp4", "image/jpeg"),
                "size": self.rng.integers(200_000, 8_000_000, media_count),
                "orientation": self.rng.choice(["landscape", "portrait", "square"], media_count),
                "filter_name": self.rng.choice(["normal", "clarendon", "lark", "juno", "valencia"], media_count),
                "filter_class": None,
                "license": "CC-BY-4.0",
                "processed_at": media_status_created,
                "hls_transcoded_at": None,
                "created_at": media_status_created,
                "updated_at": media_status_created,
                "deleted_at": None,
                "key": None,
                "metadata": [json.dumps({"width": 1080, "height": 1080, "camera": "Synthetic Camera"}) for _ in range(media_count)],
                "version": np.ones(media_count, dtype=np.int8),
            }
        )
        return statuses, media

    def generate_interactions(
        self, statuses: pd.DataFrame, profiles: pd.DataFrame, users: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        like_count = self.config.num_likes
        comment_count = self.config.num_comments
        LOGGER.info("Generating likes: %s rows; comments: %s rows", f"{like_count:,}", f"{comment_count:,}")
        profile_ids = profiles["id"].to_numpy(dtype=np.int64)
        status_ids = statuses["id"].to_numpy(dtype=np.int64)
        like_profiles, like_statuses = self._unique_pairs(profile_ids, status_ids, like_count)
        profile_created = profiles.set_index("id")["created_at"]
        status_created = statuses.set_index("id")["created_at"]
        like_parent_dates = _latest_dates(
            profile_created.loc[like_profiles].to_numpy(), status_created.loc[like_statuses].to_numpy()
        )
        like_dates = self.add_time_offset(like_parent_dates, max_days=60)
        likes = pd.DataFrame(
            {
                "id": self._make_ids(like_count),
                "profile_id": like_profiles,
                "status_id": like_statuses,
                "flagged": np.zeros(like_count, dtype=np.int8),
                "created_at": like_dates,
                "updated_at": like_dates,
                "deleted_at": None,
            }
        )

        comment_profiles = self.rng.choice(profile_ids, size=comment_count) if comment_count else np.array([], dtype=np.int64)
        comment_statuses = self.rng.choice(status_ids, size=comment_count) if comment_count else np.array([], dtype=np.int64)
        comment_parent_dates = _latest_dates(
            profile_created.loc[comment_profiles].to_numpy(), status_created.loc[comment_statuses].to_numpy()
        )
        comment_dates = self.add_time_offset(comment_parent_dates, max_days=90)
        profile_to_user = profiles.set_index("id")["user_id"]
        comment_users = profile_to_user.loc[comment_profiles].to_numpy(dtype=np.int64)
        comment_text = [self.fake.sentence(nb_words=8) for _ in range(comment_count)]
        comments = pd.DataFrame(
            {
                "id": self._make_ids(comment_count),
                "profile_id": comment_profiles,
                "user_id": comment_users,
                "status_id": comment_statuses,
                "comment": comment_text,
                "rendered": comment_text,
                "entities": None,
                "is_remote": np.zeros(comment_count, dtype=np.int8),
                "rendered_at": comment_dates,
                "created_at": comment_dates,
                "updated_at": comment_dates,
            }
        )
        return likes, comments

    def generate_social_graph_and_tags(self, profiles: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        follow_count = self.config.num_follows
        hashtag_count = self.config.num_hashtags
        LOGGER.info("Generating follows: %s rows; hashtags: %s rows", f"{follow_count:,}", f"{hashtag_count:,}")
        profile_ids = profiles["id"].to_numpy(dtype=np.int64)
        follow_profiles, following_ids = self._unique_pairs(
            profile_ids, profile_ids, follow_count, forbid_self=True
        )
        profile_created = profiles.set_index("id")["created_at"]
        follow_parent_dates = _latest_dates(
            profile_created.loc[follow_profiles].to_numpy(), profile_created.loc[following_ids].to_numpy()
        )
        follow_dates = self.add_time_offset(follow_parent_dates, max_days=365)
        followers = pd.DataFrame(
            {
                "id": self._make_ids(follow_count),
                "profile_id": follow_profiles,
                "following_id": following_ids,
                "local_profile": np.ones(follow_count, dtype=np.int8),
                "local_following": np.ones(follow_count, dtype=np.int8),
                "created_at": follow_dates,
                "updated_at": follow_dates,
            }
        )

        hashtag_names: list[str] = []
        seen_slugs: set[str] = set()
        while len(hashtag_names) < hashtag_count:
            base = re.sub(r"[^a-z0-9]+", "-", self.fake.word().lower()).strip("-") or "tag"
            candidate = base
            if candidate in seen_slugs:
                suffix = int(self.rng.integers(1, 1_000_000_000))
                candidate = f"{base}-{suffix}"
                while candidate in seen_slugs:
                    suffix += 1
                    candidate = f"{base}-{suffix}"
            seen_slugs.add(candidate)
            hashtag_names.append(candidate)

        hashtag_dates = self.random_dates(datetime(2022, 1, 1), self.run_at, hashtag_count)
        hashtags = pd.DataFrame(
            {
                "id": self._make_ids(hashtag_count),
                "name": hashtag_names,
                "slug": hashtag_names,
                "is_nsfw": np.zeros(hashtag_count, dtype=np.int8),
                "is_banned": np.zeros(hashtag_count, dtype=np.int8),
                "created_at": hashtag_dates,
                "updated_at": hashtag_dates,
            }
        )
        return followers, hashtags

    def generate_events(
        self,
        users: pd.DataFrame,
        profiles: pd.DataFrame,
        statuses: pd.DataFrame,
        media: pd.DataFrame,
        likes: pd.DataFrame,
        comments: pd.DataFrame,
        followers: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        LOGGER.info("Generating account logs, activities, notifications, and direct messages")
        user_ids = users["id"].to_numpy(dtype=np.int64)
        profile_ids = profiles["id"].to_numpy(dtype=np.int64)
        status_ids = statuses["id"].to_numpy(dtype=np.int64)
        media_ids = media["id"].to_numpy(dtype=np.int64)
        like_ids = likes["id"].to_numpy(dtype=np.int64)
        comment_ids = comments["id"].to_numpy(dtype=np.int64)
        follower_ids = followers["id"].to_numpy(dtype=np.int64)
        profile_created = profiles.set_index("id")["created_at"]
        user_created = users.set_index("id")["created_at"]

        log_count = self.config.num_logs
        log_users = self.rng.choice(user_ids, size=log_count) if log_count else np.array([], dtype=np.int64)
        log_types, log_items = self._polymorphic_items(
            log_count,
            {
                "App\\User": user_ids,
                "App\\Status": status_ids,
                "App\\Media": media_ids,
                "App\\Profile": profile_ids,
            },
        )
        log_parent_dates = user_created.loc[log_users].to_numpy()
        log_dates = self.add_time_offset(log_parent_dates, max_days=1_000)
        account_logs = pd.DataFrame(
            {
                "id": self._make_ids(log_count),
                "user_id": log_users,
                "item_id": log_items,
                "item_type": log_types,
                "action": self.rng.choice(["auth.login", "auth.logout", "password.change", "profile.update", "2fa.verify"], log_count),
                "message": [self.fake.sentence(nb_words=5) for _ in range(log_count)],
                "link": None,
                "ip_address": [self.fake.ipv4() for _ in range(log_count)],
                "user_agent": [self.fake.user_agent() for _ in range(log_count)],
                "metadata": [
                    json.dumps(
                        {
                            "browser": self.fake.chrome(),
                            "os": self.py_rng.choice(["Windows", "macOS", "Linux", "Android", "iOS"]),
                            "attempt": self.py_rng.randint(1, 3),
                        }
                    )
                    for _ in range(log_count)
                ],
                "created_at": log_dates,
                "updated_at": log_dates,
            }
        )

        activity_count = self.config.num_activities
        activity_to = self.rng.choice(profile_ids, size=activity_count) if activity_count else np.array([], dtype=np.int64)
        activity_from = self.rng.choice(profile_ids, size=activity_count) if activity_count else np.array([], dtype=np.int64)
        activity_parent_dates = _latest_dates(
            profile_created.loc[activity_to].to_numpy(), profile_created.loc[activity_from].to_numpy()
        )
        activity_dates = self.add_time_offset(activity_parent_dates, max_days=500)
        activity_actor_profiles = activity_from
        activity_object_ids = (
            self.rng.choice(status_ids, size=activity_count)
            if len(status_ids) and activity_count
            else self.rng.choice(profile_ids, size=activity_count)
            if activity_count
            else np.array([], dtype=np.int64)
        )
        activity_object_urls = (
            [f"https://pixelfed.social/p/{sid}" for sid in activity_object_ids]
            if len(status_ids)
            else [f"https://pixelfed.social/users/{pid}" for pid in activity_object_ids]
        )
        activity_data = [
            json.dumps(
                {
                    "type": "Activity",
                    "actor": f"https://pixelfed.social/users/{actor_id}",
                    "object": object_url,
                },
                separators=(",", ":"),
            )
            for actor_id, object_url in zip(activity_actor_profiles, activity_object_urls)
        ]
        activities = pd.DataFrame(
            {
                "id": self._make_ids(activity_count),
                "to_id": activity_to,
                "from_id": activity_from,
                "object_type": self.rng.choice(["Create", "Like", "Announce", "Follow", "Undo"], activity_count),
                "data": activity_data,
                "processed_at": activity_dates,
                "created_at": activity_dates,
                "updated_at": activity_dates,
            }
        )

        notification_count = self.config.num_notifications
        notification_profiles = self.rng.choice(profile_ids, size=notification_count) if notification_count else np.array([], dtype=np.int64)
        notification_actors = self.rng.choice(profile_ids, size=notification_count) if notification_count else np.array([], dtype=np.int64)
        notification_types, notification_items = self._polymorphic_items(
            notification_count,
            {
                "App\\Status": status_ids,
                "App\\Like": like_ids,
                "App\\Comment": comment_ids,
                "App\\Follower": follower_ids,
            },
        )
        notification_parent_dates = _latest_dates(
            profile_created.loc[notification_profiles].to_numpy(),
            profile_created.loc[notification_actors].to_numpy(),
        )
        notification_dates = self.add_time_offset(notification_parent_dates, max_days=500)
        read_at_values: list[pd.Timestamp | pd.NaT] = []
        for date_value in notification_dates:
            if self.py_rng.random() <= 0.30:
                read_at_values.append(pd.NaT)
            else:
                candidate = pd.Timestamp(date_value) + pd.Timedelta(minutes=self.py_rng.randint(1, 120))
                read_at_values.append(min(candidate, pd.Timestamp(self.run_at)))
        notifications = pd.DataFrame(
            {
                "id": self._make_ids(notification_count),
                "profile_id": notification_profiles,
                "actor_id": notification_actors,
                "item_id": notification_items,
                "item_type": notification_types,
                "action": self.rng.choice(["like", "comment", "mention", "follow", "reblog"], notification_count),
                "message": [self.fake.sentence(nb_words=6) for _ in range(notification_count)],
                "rendered": None,
                "read_at": pd.to_datetime(read_at_values),
                "created_at": notification_dates,
                "updated_at": notification_dates,
                "deleted_at": None,
            }
        )

        message_count = self.config.num_messages
        message_to = self.rng.choice(profile_ids, size=message_count) if message_count else np.array([], dtype=np.int64)
        message_from = self.rng.choice(profile_ids, size=message_count) if message_count else np.array([], dtype=np.int64)
        if len(status_ids) and message_count:
            message_status_ids: np.ndarray = self.rng.choice(status_ids, size=message_count)
            status_created = statuses.set_index("id")["created_at"]
            message_parent_dates = _latest_dates(
                profile_created.loc[message_to].to_numpy(),
                profile_created.loc[message_from].to_numpy(),
                status_created.loc[message_status_ids].to_numpy(),
            )
        else:
            message_status_ids = np.full(message_count, None, dtype=object)
            message_parent_dates = _latest_dates(
                profile_created.loc[message_to].to_numpy(),
                profile_created.loc[message_from].to_numpy(),
            )
        message_dates = self.add_time_offset(message_parent_dates, max_days=365)
        direct_messages = pd.DataFrame(
            {
                "id": self._make_ids(message_count),
                "to_id": message_to,
                "from_id": message_from,
                "from_profile_ids": None,
                "group_message": np.zeros(message_count, dtype=np.int8),
                "status_id": message_status_ids,
                "read_at": message_dates,
                "created_at": message_dates,
                "updated_at": message_dates,
            }
        )
        return account_logs, activities, notifications, direct_messages

    # ------------------------------------------------------------------
    # Data quality checks
    # ------------------------------------------------------------------
    @staticmethod
    def _require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    def validate_datasets(self, datasets: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
        """Fail fast on key, relationship, cardinality, and timestamp defects."""
        LOGGER.info("Running data quality checks")
        checks: list[dict[str, Any]] = []

        def record(name: str, details: str) -> None:
            checks.append({"check": name, "status": "passed", "details": details})
            LOGGER.info("DQ PASS | %s | %s", name, details)

        for table_name, frame in datasets.items():
            self._require("id" in frame.columns, f"Dataset {table_name!r} is missing its 'id' key column.")
            self._require(frame["id"].notna().all(), f"Dataset {table_name!r} contains null primary keys.")
            self._require(frame["id"].is_unique, f"Dataset {table_name!r} contains duplicate primary keys.")
            record(f"{table_name}.primary_key", f"{len(frame):,} rows; id is non-null and unique")

        expected_rows = {
            "users": self.config.num_users,
            "profiles": self.config.num_users,
            "statuses": self.config.num_statuses,
            "media": self.config.num_media,
            "comments": self.config.num_comments,
            "likes": self.config.num_likes,
            "followers": self.config.num_follows,
            "hashtags": self.config.num_hashtags,
            "account_logs": self.config.num_logs,
            "activities": self.config.num_activities,
            "notifications": self.config.num_notifications,
            "direct_messages": self.config.num_messages,
        }
        for table_name, expected in expected_rows.items():
            actual = len(datasets[table_name])
            self._require(actual == expected, f"{table_name} row-count mismatch: expected {expected:,}, got {actual:,}.")
            record(f"{table_name}.row_count", f"expected {expected:,}; found {actual:,}")

        def fk(child: str, column: str, parent: str, parent_column: str = "id", nullable: bool = False) -> None:
            child_values = datasets[child][column]
            if nullable:
                child_values = child_values.dropna()
            parent_values = set(datasets[parent][parent_column].dropna().tolist())
            invalid = ~child_values.isin(parent_values)
            self._require(
                not invalid.any(),
                f"{child}.{column} has {int(invalid.sum()):,} values without a matching {parent}.{parent_column}.",
            )
            record(f"{child}.{column}_fk", f"valid references to {parent}.{parent_column}")

        fk("profiles", "user_id", "users")
        fk("users", "profile_id", "profiles")
        fk("statuses", "profile_id", "profiles")
        fk("media", "status_id", "statuses")
        fk("media", "profile_id", "profiles")
        fk("media", "user_id", "users")
        fk("likes", "profile_id", "profiles")
        fk("likes", "status_id", "statuses")
        fk("comments", "profile_id", "profiles")
        fk("comments", "user_id", "users")
        fk("comments", "status_id", "statuses")
        fk("followers", "profile_id", "profiles")
        fk("followers", "following_id", "profiles")
        fk("account_logs", "user_id", "users")
        fk("activities", "to_id", "profiles")
        fk("activities", "from_id", "profiles")
        fk("notifications", "profile_id", "profiles")
        fk("notifications", "actor_id", "profiles")
        fk("direct_messages", "to_id", "profiles")
        fk("direct_messages", "from_id", "profiles")
        fk("direct_messages", "status_id", "statuses", nullable=True)

        polymorphic_targets = {
            "account_logs": {
                "App\\User": ("users", "id"),
                "App\\Status": ("statuses", "id"),
                "App\\Media": ("media", "id"),
                "App\\Profile": ("profiles", "id"),
            },
            "notifications": {
                "App\\Status": ("statuses", "id"),
                "App\\Like": ("likes", "id"),
                "App\\Comment": ("comments", "id"),
                "App\\Follower": ("followers", "id"),
            },
        }
        for table_name, targets in polymorphic_targets.items():
            frame = datasets[table_name]
            for entity_type, (parent_table, parent_key) in targets.items():
                mask = frame["item_type" if table_name == "account_logs" else "item_type"] == entity_type
                referenced_ids = set(datasets[parent_table][parent_key].tolist())
                invalid = ~frame.loc[mask, "item_id"].isin(referenced_ids)
                self._require(
                    not invalid.any(),
                    f"{table_name} has {int(invalid.sum()):,} invalid item_id values for {entity_type}.",
                )
            record(f"{table_name}.polymorphic_references", "item_id values match the table named by item_type")

        media_profile_lookup = datasets["statuses"].set_index("id")["profile_id"]
        expected_media_profiles = datasets["media"]["status_id"].map(media_profile_lookup)
        self._require(
            np.array_equal(
                expected_media_profiles.to_numpy(),
                datasets["media"]["profile_id"].to_numpy(),
            ),
            "media.profile_id does not match the owning status profile_id.",
        )
        record("media.status_owner_consistency", "media owner profile matches the parent status")

        for row in datasets["activities"]["data"]:
            try:
                parsed = json.loads(row)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError("activities.data contains invalid JSON.") from exc
            self._require(isinstance(parsed, dict) and parsed.get("type") == "Activity", "activities.data has an unexpected structure.")
        record("activities.data_json", "all activity payloads are valid JSON objects")

        likes = datasets["likes"]
        self._require(not likes.duplicated(["profile_id", "status_id"]).any(), "Duplicate profile/status like pairs detected.")
        record("likes.unique_pair", "each profile likes a given status at most once")
        follows = datasets["followers"]
        self._require(not follows.duplicated(["profile_id", "following_id"]).any(), "Duplicate follow pairs detected.")
        self._require(not (follows["profile_id"] == follows["following_id"]).any(), "Self-follow rows detected.")
        record("followers.unique_pair", "follow pairs are unique and contain no self-follows")

        for column in ("username", "email"):
            self._require(datasets["users"][column].is_unique, f"users.{column} contains duplicates.")
            record(f"users.{column}_unique", f"{column} values are unique")
        self._require(datasets["statuses"]["uri"].is_unique, "statuses.uri contains duplicates.")
        record("statuses.uri_unique", "status URIs are unique")
        self._require(datasets["hashtags"]["slug"].is_unique, "hashtags.slug contains duplicates.")
        record("hashtags.slug_unique", "hashtag slugs are unique")

        now = pd.Timestamp(self.run_at)
        for table_name, frame in datasets.items():
            for column in frame.columns:
                if column.endswith("_at") and pd.api.types.is_datetime64_any_dtype(frame[column]):
                    future_count = int((frame[column].dropna() > now).sum())
                    self._require(
                        future_count == 0,
                        f"{table_name}.{column} contains {future_count:,} timestamps after run time.",
                    )
        record("timestamps.not_future", "all datetime-typed *_at columns are no later than the run timestamp")
        return checks

    # ------------------------------------------------------------------
    # Exports and manifest
    # ------------------------------------------------------------------
    @staticmethod
    def _sqlite_type(series: pd.Series) -> str:
        if pd.api.types.is_bool_dtype(series.dtype) or pd.api.types.is_integer_dtype(series.dtype):
            return "INTEGER"
        if pd.api.types.is_float_dtype(series.dtype):
            return "REAL"
        return "TEXT"

    @staticmethod
    def _quote_identifier(value: str) -> str:
        return '"' + value.replace('"', '""') + '"'

    @staticmethod
    def _sqlite_ready(frame: pd.DataFrame) -> pd.DataFrame:
        """Convert timestamps to ISO text for portable SQLite storage."""
        result = frame.copy()
        for column in result.columns:
            if pd.api.types.is_datetime64_any_dtype(result[column]):
                result[column] = result[column].dt.strftime("%Y-%m-%dT%H:%M:%S")
        return result.astype(object).where(pd.notna(result), None)

    def _export_sqlite(self, datasets: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
        sqlite_dir = output_dir / "relational_sqlite"
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        final_path = sqlite_dir / "pixelfed_source_snapshot.sqlite"
        temp_path = sqlite_dir / "pixelfed_source_snapshot.sqlite.tmp"
        if temp_path.exists():
            temp_path.unlink()

        foreign_keys_by_table = self.SQLITE_FOREIGN_KEYS
        with sqlite3.connect(temp_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = DELETE")
            for table_name in self.SQLITE_ORDER:
                frame = self._sqlite_ready(datasets[table_name])
                definitions: list[str] = []
                for column in frame.columns:
                    quoted = self._quote_identifier(column)
                    column_type = self._sqlite_type(frame[column])
                    if column == "id":
                        definitions.append(f"{quoted} INTEGER PRIMARY KEY")
                    else:
                        definitions.append(f"{quoted} {column_type}")
                for child_col, parent_table, parent_col in foreign_keys_by_table.get(table_name, ()):
                    definitions.append(
                        f"FOREIGN KEY ({self._quote_identifier(child_col)}) "
                        f"REFERENCES {self._quote_identifier(parent_table)} ({self._quote_identifier(parent_col)})"
                    )
                connection.execute(
                    f"CREATE TABLE {self._quote_identifier(table_name)} ({', '.join(definitions)})"
                )
                # Keep each multi-row INSERT below SQLite's conservative 999-variable limit.
                safe_chunksize = max(1, min(1_000, 900 // max(1, len(frame.columns))))
                frame.to_sql(
                    table_name,
                    connection,
                    if_exists="append",
                    index=False,
                    method="multi",
                    chunksize=safe_chunksize,
                )

            # Business-key constraints and common join/filter indexes.
            connection.execute('CREATE UNIQUE INDEX idx_users_username ON users (username)')
            connection.execute('CREATE UNIQUE INDEX idx_users_email ON users (email)')
            connection.execute('CREATE UNIQUE INDEX idx_profiles_username ON profiles (username)')
            connection.execute('CREATE UNIQUE INDEX idx_statuses_uri ON statuses (uri)')
            connection.execute('CREATE UNIQUE INDEX idx_likes_profile_status ON likes (profile_id, status_id)')
            connection.execute('CREATE UNIQUE INDEX idx_followers_profile_following ON followers (profile_id, following_id)')
            for table, column in (
                ("profiles", "user_id"),
                ("statuses", "profile_id"),
                ("media", "status_id"),
                ("likes", "status_id"),
                ("comments", "status_id"),
                ("followers", "following_id"),
                ("notifications", "profile_id"),
                ("direct_messages", "to_id"),
            ):
                connection.execute(
                    f"CREATE INDEX {self._quote_identifier(f'idx_{table}_{column}')} "
                    f"ON {self._quote_identifier(table)} ({self._quote_identifier(column)})"
                )

            fk_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if fk_violations:
                raise ValueError(f"SQLite foreign-key check failed: {fk_violations[:5]!r}")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise ValueError(f"SQLite integrity check failed: {integrity!r}")

        # sqlite3's context manager commits/rolls back but does not close the connection.
        connection.close()
        temp_path.replace(final_path)
        LOGGER.info("Exported SQLite snapshot with %d tables: %s", len(self.SQLITE_ORDER), final_path)
        return {
            "format": "sqlite",
            "path": str(final_path),
            "tables": len(self.SQLITE_ORDER),
            "rows": int(sum(len(datasets[name]) for name in self.SQLITE_ORDER)),
            "size_bytes": final_path.stat().st_size,
        }

    @staticmethod
    def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
        temp_path = path.with_name(path.name + ".tmp")
        with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)
            handle.write("\n")
        temp_path.replace(path)

    def export_datasets(
        self, datasets: dict[str, pd.DataFrame], output_dir: Path, checks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        files: list[dict[str, Any]] = []

        for group_name, table_names in self.EXPORT_GROUPS.items():
            group_dir = output_dir / group_name
            group_dir.mkdir(parents=True, exist_ok=True)
            for table_name in table_names:
                frame = datasets[table_name]
                if group_name == "batch_csv_gz":
                    path = group_dir / f"{table_name}.csv.gz"
                    temp_path = path.with_name(path.name + ".tmp")
                    frame.to_csv(temp_path, index=False, compression="gzip", date_format="%Y-%m-%dT%H:%M:%S")
                    file_format = "csv.gz"
                elif group_name == "columnar_parquet":
                    path = group_dir / f"{table_name}.parquet"
                    temp_path = path.with_name(path.name + ".tmp")
                    frame.to_parquet(temp_path, engine="pyarrow", compression="snappy", index=False)
                    file_format = "parquet"
                elif group_name == "streaming_jsonl":
                    path = group_dir / f"{table_name}.jsonl"
                    temp_path = path.with_name(path.name + ".tmp")
                    frame.to_json(
                        temp_path,
                        orient="records",
                        lines=True,
                        date_format="iso",
                        date_unit="us",
                        force_ascii=False,
                    )
                    file_format = "jsonl"
                else:
                    # pandas.to_feather writes the Feather IPC format; use a .feather suffix.
                    path = group_dir / f"{table_name}.feather"
                    temp_path = path.with_name(path.name + ".tmp")
                    frame.reset_index(drop=True).to_feather(temp_path, compression="zstd")
                    file_format = "feather"

                temp_path.replace(path)
                file_info = {
                    "table": table_name,
                    "format": file_format,
                    "path": str(path),
                    "rows": len(frame),
                    "columns": len(frame.columns),
                    "size_bytes": path.stat().st_size,
                }
                files.append(file_info)
                LOGGER.info("Exported %-18s | %8s rows | %-8s | %s", table_name, f"{len(frame):,}", file_format, path)

        files.append(self._export_sqlite(datasets, output_dir))
        manifest = {
            "project": "PixelFed Synthetic Data Lakehouse",
            "schema_version": "1.0.0",
            "generated_at_utc": self.generated_at.isoformat() + "Z",
            "as_of_utc": self.run_at.isoformat() + "Z",
            "seed": self.config.seed,
            "output_dir": str(output_dir),
            "configuration": {
                field: getattr(self.config, field) if field != "output_dir" else str(self.config.output_dir)
                for field in self.config.count_fields
            },
            "row_counts": {name: int(len(frame)) for name, frame in datasets.items()},
            "quality_checks": checks,
            "files": files,
            "notes": [
                "All records are synthetic and intended for engineering demos, testing, and learning.",
                "Datetime columns in tabular files represent UTC but are timezone-naive for broad engine compatibility.",
                "JSONL event timestamps are serialized as ISO strings.",
                "The binary export is Apache Feather IPC and uses the .feather extension.",
            ],
        }
        self._write_json_atomic(output_dir / "manifest.json", manifest)
        self._write_json_atomic(
            output_dir / "data_quality_report.json",
            {
                "generated_at_utc": manifest["generated_at_utc"],
                "as_of_utc": manifest["as_of_utc"],
                "status": "passed",
                "check_count": len(checks),
                "checks": checks,
            },
        )
        return manifest

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run(self) -> dict[str, Any]:
        output_dir = self.config.output_dir.expanduser().resolve()
        LOGGER.info("Starting PixelFed lakehouse generation | seed=%s | output=%s", self.config.seed, output_dir)

        users, profiles = self.generate_users_and_profiles()
        statuses, media = self.generate_statuses_and_media(profiles, users)
        likes, comments = self.generate_interactions(statuses, profiles, users)
        followers, hashtags = self.generate_social_graph_and_tags(profiles)
        account_logs, activities, notifications, direct_messages = self.generate_events(
            users, profiles, statuses, media, likes, comments, followers
        )

        datasets = {
            "users": users,
            "profiles": profiles,
            "statuses": statuses,
            "media": media,
            "likes": likes,
            "comments": comments,
            "followers": followers,
            "hashtags": hashtags,
            "account_logs": account_logs,
            "activities": activities,
            "notifications": notifications,
            "direct_messages": direct_messages,
        }
        checks = self.validate_datasets(datasets)
        manifest = self.export_datasets(datasets, output_dir, checks)
        LOGGER.info("Generation completed successfully. Wrote %d exports.", len(manifest["files"]))
        LOGGER.info("Manifest: %s", output_dir / "manifest.json")
        return manifest


def _parse_as_of(value: str) -> datetime:
    """Parse an ISO 8601 date/time; timezone-aware values are normalized to UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--as-of must be an ISO 8601 timestamp, for example 2026-10-14T12:00:00Z."
        ) from exc
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def parse_args(argv: list[str] | None = None) -> GeneratorConfig:
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic PixelFed datasets for a multi-format lakehouse."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("pixelfed_lakehouse_landing"), help="Output directory (default: ./pixelfed_lakehouse_landing).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible values (default: 42).")
    parser.add_argument(
        "--as-of",
        type=_parse_as_of,
        default=None,
        help="Optional fixed UTC anchor, e.g. 2026-10-14T12:00:00Z; combine with --seed for repeatable timestamps.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale every configured row count (e.g. 0.01 for a smoke-test dataset; default: 1.0).",
    )
    args = parser.parse_args(argv)
    if not np.isfinite(args.scale) or args.scale <= 0:
        parser.error("--scale must be a positive finite number.")

    base = GeneratorConfig(seed=args.seed, output_dir=args.output_dir, as_of=args.as_of)
    if args.scale != 1.0:
        scaled_counts = {
            field: max(1, int(round(getattr(base, field) * args.scale)))
            for field in base.count_fields
        }
        base = replace(base, **scaled_counts)
    try:
        base.validate()
    except ValueError as exc:
        parser.error(str(exc))
    return base


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    config = parse_args(argv)
    try:
        manifest = PixelFedLakehouseGenerator(config).run()
    except ImportError as exc:
        LOGGER.error("A required dependency is missing: %s", exc)
        LOGGER.error("Install dependencies with: python -m pip install -r requirements.txt")
        return 2
    except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
        LOGGER.exception("Pipeline failed: %s", exc)
        return 1

    total_rows = sum(manifest["row_counts"].values())
    print("\nPIXELFED LAKEHOUSE GENERATION SUCCEEDED")
    print(f"Output directory : {Path(manifest['output_dir'])}")
    print(f"Total rows       : {total_rows:,}")
    print(f"Export files     : {len(manifest['files']):,}")
    print(f"Quality checks   : {len(manifest['quality_checks']):,} passed")
    print(f"Manifest         : {Path(manifest['output_dir']) / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
