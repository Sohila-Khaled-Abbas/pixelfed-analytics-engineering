#!/usr/bin/env python3
"""Internal schema-driven synthetic row generator.

Use ``src/generate_landing.py`` as the CLI entry point. This module generates
records and validates the supplied schema contract; the project wrapper owns the
fixed one-table/one-format export policy.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import logging
import random
import re
import shutil
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from faker import Faker

LOG = logging.getLogger("pixelfed_schema_lakehouse")
DEFAULT_OUTPUT = r"D:\courses\Data Analysis 26-27\Projects\PixelFed\data\landing"

# Base volumes are deliberately practical for a local Power BI portfolio project.
# --scale multiplies each value; every table keeps at least one row at positive scales.
BASE_COUNTS: dict[str, int] = {
    "account_logs": 3000,
    "activities": 3500,
    "avatars": 350,
    "bookmarks": 2000,
    "circle_profiles": 500,
    "circles": 120,
    "collection_items": 600,
    "collections": 180,
    "comments": 12000,
    "contacts": 80,
    "direct_messages": 1500,
    "discover_categories": 25,
    "discover_category_hashtags": 100,
    "email_verifications": 80,
    "failed_jobs": 40,
    "follow_requests": 250,
    "followers": 8000,
    "hashtag_follows": 1200,
    "hashtags": 150,
    "import_datas": 100,
    "import_jobs": 60,
    "instances": 12,
    "jobs": 100,
    "likes": 25000,
    "media": 8000,
    "mentions": 3000,
    "migrations": 35,
    "mod_logs": 200,
    "newsroom": 40,
    "notifications": 5000,
    "oauth_access_tokens": 1000,
    "oauth_auth_codes": 200,
    "oauth_clients": 20,
    "oauth_personal_access_clients": 5,
    "oauth_refresh_tokens": 700,
    "pages": 75,
    "password_resets": 50,
    "places": 100,
    "profile_sponsors": 40,
    "profiles": 1200,
    "report_comments": 100,
    "report_logs": 300,
    "reports": 100,
    "sessions": 400,
    "status_hashtags": 4000,
    "statuses": 6000,
    "stories": 1000,
    "story_views": 4000,
    "user_devices": 600,
    "user_filters": 500,
    "user_invites": 60,
    "user_settings": 500,
    "users": 1000,
    "websockets_statistics_entries": 500,
}

DEFAULT_FORMATS = "csv,csv_gz,parquet,jsonl,feather,sqlite"
EVENT_TABLES = (
    "account_logs",
    "activities",
    "failed_jobs",
    "jobs",
    "mod_logs",
    "notifications",
    "report_logs",
    "websockets_statistics_entries",
)
FEATHER_TABLES = ("direct_messages",)

TYPE_PATTERN = re.compile(r"^\s*([A-Za-z0-9_]+):\s*(.*?)\s*$")
TABLE_PATTERN = re.compile(r"^##\s+([A-Za-z0-9_]+)\s*$", re.M)
RELATION_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*→\s*"
    r"([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*\((one-to-many|many-to-one)\)\s*$"
)
INDEX_PATTERN = re.compile(r"^\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*\((unique|index)\):\s*(.*?)\s*$")


@dataclass(frozen=True)
class ColumnDef:
    name: str
    mysql_type: str
    nullable: bool
    primary_key: bool
    unique: bool
    indexed: bool
    foreign_key_marker: bool


@dataclass
class TableDef:
    name: str
    columns: list[ColumnDef]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def col(self, name: str) -> ColumnDef:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(f"{self.name}.{name} is not in the schema")


@dataclass
class SchemaContract:
    tables: dict[str, TableDef]
    # (table, columns, unique, index_name)
    indexes: list[tuple[str, tuple[str, ...], bool, str]]
    # Normalized as (child_table, child_column, parent_table, parent_column)
    relationships: list[tuple[str, str, str, str]]


def parse_schema(path: Path) -> SchemaContract:
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}. Keep schema.md beside this script or use --schema.")
    content = path.read_text(encoding="utf-8")
    sections = re.split(r"^##\s+", content, flags=re.M)
    tables: dict[str, TableDef] = {}
    in_metadata = False
    for section in sections[1:]:
        title = section.splitlines()[0].strip()
        if title in {"Relationships", "Indexes"}:
            in_metadata = True
            continue
        if in_metadata:
            continue
        cols: list[ColumnDef] = []
        for line in section.splitlines()[1:]:
            m = TYPE_PATTERN.match(line)
            if not m:
                continue
            col_name, remainder = m.groups()
            tokens = remainder.split()
            if not tokens:
                continue
            mysql_type = tokens[0].lower()
            token_set = {t.lower().strip(",") for t in tokens[1:]}
            cols.append(
                ColumnDef(
                    name=col_name,
                    mysql_type=mysql_type,
                    nullable="nullable" in token_set,
                    primary_key="pk" in token_set,
                    unique="unique" in token_set,
                    indexed="indexed" in token_set,
                    foreign_key_marker="fk" in token_set,
                )
            )
        if cols:
            tables[title] = TableDef(title, cols)

    if len(tables) != 54:
        raise ValueError(f"Expected 54 table definitions in schema.md; parsed {len(tables)}.")

    relationships: list[tuple[str, str, str, str]] = []
    if "## Relationships" in content:
        relationship_section = content.split("## Relationships", 1)[1].split("## Indexes", 1)[0]
        for line in relationship_section.splitlines():
            match = RELATION_PATTERN.match(line)
            if not match:
                continue
            left_table, left_col, right_table, right_col, rel_type = match.groups()
            if rel_type == "one-to-many":
                relationships.append((right_table, right_col, left_table, left_col))
            else:  # many-to-one: left side is the FK / many side.
                relationships.append((left_table, left_col, right_table, right_col))

    indexes: list[tuple[str, tuple[str, ...], bool, str]] = []
    if "## Indexes" in content:
        index_section = content.split("## Indexes", 1)[1]
        for line in index_section.splitlines():
            match = INDEX_PATTERN.match(line)
            if not match:
                continue
            table_name, index_name, index_type, columns_raw = match.groups()
            column_names = tuple(c.strip() for c in columns_raw.split(",") if c.strip())
            if table_name in tables and column_names:
                indexes.append((table_name, column_names, index_type == "unique", index_name))

    # Validate the metadata against the exact column inventory before generating data.
    for table_name, table in tables.items():
        for col in table.columns:
            if not col.mysql_type:
                raise ValueError(f"Missing type: {table_name}.{col.name}")
    for child_table, child_col, parent_table, parent_col in relationships:
        if child_table not in tables or parent_table not in tables:
            raise ValueError(f"Unknown table in relationship: {child_table}.{child_col} -> {parent_table}.{parent_col}")
        tables[child_table].col(child_col)
        tables[parent_table].col(parent_col)
    for table_name, cols, _unique, index_name in indexes:
        if table_name not in tables:
            raise ValueError(f"Unknown table in index: {index_name}")
        for col_name in cols:
            tables[table_name].col(col_name)

    return SchemaContract(tables=tables, indexes=indexes, relationships=relationships)


# Additional conventional links for columns marked FK in the column inventory but not
# fully represented in the Relationships section. Explicit documented relationships win.
CONVENTIONAL_REFERENCES: dict[tuple[str, str], tuple[str, str]] = {
    ("users", "profile_id"): ("profiles", "id"),
    ("profiles", "user_id"): ("users", "id"),
    ("account_logs", "user_id"): ("users", "id"),
    ("avatars", "profile_id"): ("profiles", "id"),
    ("bookmarks", "status_id"): ("statuses", "id"),
    ("bookmarks", "profile_id"): ("profiles", "id"),
    ("circle_profiles", "circle_id"): ("circles", "id"),
    ("circle_profiles", "profile_id"): ("profiles", "id"),
    ("circles", "profile_id"): ("profiles", "id"),
    ("collection_items", "collection_id"): ("collections", "id"),
    ("collections", "profile_id"): ("profiles", "id"),
    ("comments", "profile_id"): ("profiles", "id"),
    ("comments", "user_id"): ("users", "id"),
    ("comments", "status_id"): ("statuses", "id"),
    ("contacts", "user_id"): ("users", "id"),
    ("direct_messages", "status_id"): ("statuses", "id"),
    ("discover_categories", "media_id"): ("media", "id"),
    ("discover_category_hashtags", "discover_category_id"): ("discover_categories", "id"),
    ("discover_category_hashtags", "hashtag_id"): ("hashtags", "id"),
    ("email_verifications", "user_id"): ("users", "id"),
    ("follow_requests", "follower_id"): ("followers", "id"),
    ("followers", "profile_id"): ("profiles", "id"),
    ("hashtag_follows", "user_id"): ("users", "id"),
    ("hashtag_follows", "profile_id"): ("profiles", "id"),
    ("hashtag_follows", "hashtag_id"): ("hashtags", "id"),
    ("import_datas", "profile_id"): ("profiles", "id"),
    ("import_datas", "job_id"): ("jobs", "id"),
    ("import_jobs", "profile_id"): ("profiles", "id"),
    ("likes", "profile_id"): ("profiles", "id"),
    ("likes", "status_id"): ("statuses", "id"),
    ("media", "status_id"): ("statuses", "id"),
    ("media", "profile_id"): ("profiles", "id"),
    ("media", "user_id"): ("users", "id"),
    ("mentions", "status_id"): ("statuses", "id"),
    ("mentions", "profile_id"): ("profiles", "id"),
    ("mod_logs", "user_id"): ("users", "id"),
    ("newsroom", "user_id"): ("users", "id"),
    ("notifications", "profile_id"): ("profiles", "id"),
    ("oauth_access_tokens", "user_id"): ("users", "id"),
    ("oauth_refresh_tokens", "access_token_id"): ("oauth_access_tokens", "id"),
    ("oauth_auth_codes", "user_id"): ("users", "id"),
    ("oauth_clients", "user_id"): ("users", "id"),
    ("pages", "category_id"): ("discover_categories", "id"),
    ("profile_sponsors", "profile_id"): ("profiles", "id"),
    ("report_comments", "report_id"): ("reports", "id"),
    ("report_comments", "profile_id"): ("profiles", "id"),
    ("report_comments", "user_id"): ("users", "id"),
    ("report_logs", "profile_id"): ("profiles", "id"),
    ("reports", "profile_id"): ("profiles", "id"),
    ("reports", "user_id"): ("users", "id"),
    ("sessions", "user_id"): ("users", "id"),
    ("status_hashtags", "status_id"): ("statuses", "id"),
    ("status_hashtags", "hashtag_id"): ("hashtags", "id"),
    ("status_hashtags", "profile_id"): ("profiles", "id"),
    ("statuses", "profile_id"): ("profiles", "id"),
    ("statuses", "place_id"): ("places", "id"),
    ("stories", "profile_id"): ("profiles", "id"),
    ("story_views", "story_id"): ("stories", "id"),
    ("story_views", "profile_id"): ("profiles", "id"),
    ("user_devices", "user_id"): ("users", "id"),
    ("user_filters", "user_id"): ("users", "id"),
    ("user_invites", "user_id"): ("users", "id"),
    ("user_invites", "profile_id"): ("profiles", "id"),
    ("user_settings", "user_id"): ("users", "id"),
}

# These names have natural target tables even where the Markdown does not label them FK.
SEMANTIC_REFERENCES: dict[tuple[str, str], tuple[str, str]] = {
    ("activities", "to_id"): ("profiles", "id"),
    ("activities", "from_id"): ("profiles", "id"),
    ("direct_messages", "to_id"): ("profiles", "id"),
    ("direct_messages", "from_id"): ("profiles", "id"),
    ("notifications", "actor_id"): ("profiles", "id"),
    ("circles", "profile_id"): ("profiles", "id"),
    ("followers", "following_id"): ("profiles", "id"),
    ("follow_requests", "following_id"): ("profiles", "id"),
    ("oauth_access_tokens", "client_id"): ("oauth_clients", "id"),
    ("oauth_auth_codes", "client_id"): ("oauth_clients", "id"),
    ("oauth_personal_access_clients", "client_id"): ("oauth_clients", "id"),
    ("statuses", "in_reply_to_id"): ("statuses", "id"),
    ("statuses", "reblog_of_id"): ("statuses", "id"),
    # This field identifies the profile reported, not an independent arbitrary bigint.
    ("reports", "reported_profile_id"): ("profiles", "id"),
}

# Semantic corrections to relationships that are misrepresented by a source-schema
# inference. In PixelFed, a follow request's follower_id and following_id are profile IDs;
# the follower row's own id is the relationship-record PK, not the follower identity.
SEMANTIC_REFERENCE_OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {
    ("follow_requests", "follower_id"): ("profiles", "id"),
}

FLAG_NAMES = {
    "is_admin",
    "is_nsfw",
    "is_remote",
    "remote_media",
    "local_profile",
    "local_following",
    "is_rejected",
    "is_local",
    "flagged",
    "unlisted",
    "cw",
    "no_autolink",
    "is_private",
    "is_suggestable",
    "comments_disabled",
    "response_requested",
    "group_message",
    "active",
    "no_nsfw",
    "local_only",
    "public_only",
    "photos_only",
    "import_accepted",
    "banned",
    "auto_cw",
    "revoked",
    "personal_access_client",
    "password_client",
    "cached",
    "force_modal",
    "show_timeline",
    "show_link",
    "auth_only",
    "system_message",
    "admin_seen",
    "not_interested",
    "spam",
    "abusive",
    "nsfw",
    "public",
    "trusted",
    "crawlable",
    "show_guests",
    "show_discover",
    "public_dm",
    "hide_cw_search",
    "hide_blocked_search",
    "always_show_cw",
    "compose_media_descriptions",
    "reduce_motion",
    "optimize_screen_reader",
    "high_contrast_mode",
    "video_autoplay",
    "send_email_new_follower",
    "send_email_new_follower_request",
    "send_email_on_share",
    "send_email_on_like",
    "send_email_on_mention",
    "show_profile_followers",
    "show_profile_follower_count",
    "show_profile_following",
    "show_profile_following_count",
    "2fa_enabled",
    "deleted",
    "read",
}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


class SchemaDrivenGenerator:
    def __init__(
        self,
        schema: SchemaContract,
        output_dir: Path,
        seed: int,
        scale: float,
        as_of: datetime | None,
        formats: set[str],
    ) -> None:
        if scale <= 0:
            raise ValueError("--scale must be greater than 0")
        unknown_formats = formats - {"csv", "csv_gz", "parquet", "jsonl", "feather", "sqlite"}
        if unknown_formats:
            raise ValueError(f"Unknown formats: {', '.join(sorted(unknown_formats))}")
        self.schema = schema
        self.output_dir = output_dir
        self.seed = seed
        self.scale = scale
        self.formats = formats
        self.py_rng = random.Random(seed)
        self.fake = Faker()
        self.fake.seed_instance(seed)
        self.run_at = as_of or datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        if self.run_at.tzinfo is not None:
            self.run_at = self.run_at.astimezone(timezone.utc).replace(tzinfo=None)
        self.run_at = self.run_at.replace(microsecond=0)
        self.start_at = datetime(2022, 1, 1)
        self.row_counts = {name: max(1, int(round(BASE_COUNTS.get(name, 100) * scale))) for name in schema.tables}
        # Preserve a local host plus at least one federated host even in tiny smoke-test runs.
        if "instances" in self.row_counts:
            self.row_counts["instances"] = max(2, self.row_counts["instances"])
        self.references = self._build_references()
        self.unique_columns = self._build_unique_columns()
        self.unique_indexes = [x for x in schema.indexes if x[2] and len(x[1]) > 1]
        self.identity_values: dict[tuple[str, str], list[Any]] = {}
        self.datasets: dict[str, list[dict[str, Any]]] = {}
        self._persona_cache: dict[str, dict[str, str]] = {}
        self._allocate_primary_keys()
        self._allocate_unique_columns()

    def _build_references(self) -> dict[tuple[str, str], tuple[str, str]]:
        refs = dict(SEMANTIC_REFERENCES)
        refs.update(CONVENTIONAL_REFERENCES)
        # Declared Relationships are authoritative, even if a relationship looks unusual.
        for child_table, child_col, parent_table, parent_col in self.schema.relationships:
            refs[(child_table, child_col)] = (parent_table, parent_col)
        # Correct known semantic inference errors while preserving the schema's columns/types.
        refs.update(SEMANTIC_REFERENCE_OVERRIDES)
        # Only apply conventional metadata references where columns exist.
        for (table, col), (parent, pcol) in list(refs.items()):
            if table not in self.schema.tables or parent not in self.schema.tables:
                refs.pop((table, col), None)
                continue
            if col not in self.schema.tables[table].column_names or pcol not in self.schema.tables[parent].column_names:
                refs.pop((table, col), None)
        return refs

    def _build_unique_columns(self) -> dict[str, set[str]]:
        unique: dict[str, set[str]] = defaultdict(set)
        for table_name, table in self.schema.tables.items():
            for col in table.columns:
                if col.unique or col.primary_key:
                    unique[table_name].add(col.name)
        for table_name, cols, is_unique, _name in self.schema.indexes:
            if is_unique and len(cols) == 1:
                unique[table_name].add(cols[0])
        return unique

    def _stable_persona(self, key: str) -> dict[str, str]:
        """Return reproducible, plausible synthetic account attributes for one entity key."""
        if key not in self._persona_cache:
            seed_bytes = hashlib.sha256(f"{self.seed}:persona:{key}".encode()).digest()
            persona_seed = int.from_bytes(seed_bytes[:8], "big")
            persona_fake = Faker()
            persona_fake.seed_instance(persona_seed)
            base_handle = re.sub(r"[^a-z0-9_]+", "", persona_fake.user_name().lower()) or "member"
            suffix = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
            username = f"{base_handle[:20]}_{suffix}"
            self._persona_cache[key] = {
                "name": persona_fake.name(),
                "username": username,
                "email": f"{username}@example.test",
            }
        return self._persona_cache[key]

    def _identity_value(self, table: str, col: ColumnDef, idx: int) -> Any:
        name = col.name
        t = col.mysql_type
        n = idx + 1
        if t in {"tinyint", "smallint", "int", "integer", "bigint"}:
            if name in FLAG_NAMES:
                return idx % 2
            return n
        if name in {"email", "response"} and "email" in name:
            return f"{table}_{n:06d}@example.test"
        if name in {"username", "user_username"}:
            return f"{table}_user_{n:06d}"
        if name == "name":
            return f"{table.replace('_', ' ').title()} {n:05d}"
        if name in {"domain", "slug"}:
            if name == "domain":
                return f"instance-{n:05d}.example.test"
            return f"{table.replace('_', '-')}-{n:05d}"
        if name == "uri":
            return f"https://pixelfed.example.test/{table}/{n:08d}"
        if name == "webfinger":
            return f"@profile_{n:06d}@pixelfed.example.test"
        if name.endswith("_url") or name in {"url", "website", "link", "redirect", "admin_url"}:
            return f"https://example.test/{table}/{name}/{n:06d}"
        if name in {"key_id"}:
            return f"https://example.test/keys/{n:06d}#main-key"
        if name == "id" and t in {"varchar", "text", "longtext"}:
            return hashlib.sha256(f"{self.seed}|{table}|{name}|{n}".encode()).hexdigest()[:40]
        if name in {"token", "user_token", "random_token", "key", "fingerprint", "secret"}:
            return hashlib.sha256(f"{self.seed}|{table}|{name}|{n}".encode()).hexdigest()
        if t in {"varchar", "text", "longtext", "json", "enum"}:
            return f"{table}_{name}_{n:06d}"
        if t in {"decimal", "float", "double", "real"}:
            return round((idx + 1) / 1000, 6)
        return f"{table}_{name}_{n:06d}"

    def _allocate_primary_keys(self) -> None:
        for table_name, table in self.schema.tables.items():
            count = self.row_counts[table_name]
            for col in table.columns:
                if col.primary_key:
                    self.identity_values[(table_name, col.name)] = [
                        self._identity_value(table_name, col, i) for i in range(count)
                    ]

    def _allocate_unique_columns(self) -> None:
        # Allocate declared unique keys before row generation so foreign keys may point to them.
        for table_name, table in self.schema.tables.items():
            count = self.row_counts[table_name]
            for col_name in self.unique_columns.get(table_name, set()):
                if (table_name, col_name) in self.identity_values:
                    continue
                col = table.col(col_name)
                ref = self.references.get((table_name, col_name))
                if ref and ref in self.identity_values:
                    target_vals = self.identity_values[ref]
                    if len(target_vals) < count:
                        if not col.nullable:
                            raise ValueError(
                                f"Cannot satisfy unique FK {table_name}.{col_name}: "
                                f"{count} rows but only {len(target_vals)} parent keys. Lower --scale."
                            )
                        vals = list(target_vals) + [None] * (count - len(target_vals))
                    else:
                        vals = list(target_vals[:count])
                        self.py_rng.shuffle(vals)
                    self.identity_values[(table_name, col_name)] = vals
                else:
                    vals = [self._identity_value(table_name, col, i) for i in range(count)]
                    self.identity_values[(table_name, col_name)] = vals

    def _target_values(self, table: str, col: str) -> list[Any]:
        ref = self.references.get((table, col))
        if not ref:
            return []
        target_table, target_col = ref
        return self.identity_values.get((target_table, target_col), [])

    def _timestamp_value(self, table: str, col: str, idx: int) -> str:
        # Stable pseudo-random time that respects this run's as-of date.
        span_seconds = max(1, int((self.run_at - self.start_at).total_seconds()))
        digest = hashlib.sha256(f"{self.seed}:{table}:{col}:{idx}".encode()).digest()
        offset = int.from_bytes(digest[:8], "big") % span_seconds
        dt = self.start_at + timedelta(seconds=offset)
        if col in {"updated_at", "processed_at", "rendered_at", "last_processed_at", "last_fetched_at"}:
            dt = min(self.run_at, dt + timedelta(days=1))
        return dt.replace(microsecond=0).isoformat(sep=" ")

    def _random_ref_value(self, table: str, col: ColumnDef) -> Any:
        target_values = self._target_values(table, col.name)
        if not target_values:
            return None if col.nullable else 1
        if col.nullable and self.py_rng.random() < 0.035 and col.name not in self.unique_columns.get(table, set()):
            return None
        return self.py_rng.choice(target_values)

    def _scalar_value(self, table: str, col: ColumnDef, idx: int, force_unique: bool = False) -> Any:
        name, t = col.name, col.mysql_type
        if (table, name) in self.identity_values:
            return self.identity_values[(table, name)][idx]
        if (table, name) in self.references:
            return self._random_ref_value(table, col)

        nullable_rate = 0.06
        if col.nullable and not force_unique:
            # Strong null patterns for lifecycle/optional metadata fields.
            if name in {
                "deleted_at",
                "delete_after",
                "last_fetched_at",
                "last_processed_at",
                "hls_transcoded_at",
                "read_at",
                "responded_at",
                "completed_at",
                "reserved_at",
                "remote_url",
                "private_key",
                "public_key",
                "2fa_secret",
                "2fa_setup_at",
                "2fa_backup_codes",
                "sharedInbox",
                "inbox_url",
            }:
                nullable_rate = 0.70 if name not in {"inbox_url"} else 0.04
            elif name in {"domain", "place_id", "user_id", "profile_id", "status_id", "job_id", "published_at"}:
                nullable_rate = 0.04
            if self.py_rng.random() < nullable_rate:
                return None

        if t in {"timestamp", "datetime"}:
            if (
                name
                in {
                    "deleted_at",
                    "last_fetched_at",
                    "last_processed_at",
                    "hls_transcoded_at",
                    "read_at",
                    "responded_at",
                    "completed_at",
                    "last_active_at",
                    "used_at",
                    "reserved_at",
                    "delete_after",
                    "active_until",
                    "valid_until",
                }
                and self.py_rng.random() < 0.7
            ):
                return None
            return self._timestamp_value(table, name, idx)
        if name in {"last_activity", "available_at", "created_at"} and t in {"int", "bigint", "smallint"}:
            return int(self.run_at.timestamp()) - self.py_rng.randint(0, 60 * 60 * 24 * 60)
        if t in {"tinyint", "smallint", "int", "integer", "bigint"}:
            if (
                name in FLAG_NAMES
                or name.startswith("is_")
                or name.startswith("show_")
                or name.startswith("send_email_")
                or name.endswith("_only")
            ):
                return int(
                    self.py_rng.random() < (0.08 if name in {"is_admin", "banned", "spam", "abusive", "nsfw"} else 0.5)
                )
            if name in {"size", "peak_connection_count", "websocket_message_count", "api_message_count"}:
                return self.py_rng.randint(0, 8_000_000 if name == "size" else 20_000)
            if name in {
                "attempts",
                "change_count",
                "stage",
                "batch",
                "order",
                "duration",
                "version",
                "client_id",
                "category_id",
                "filterable_id",
                "object_id",
                "item_id",
                "application_id",
                "conversation_id",
            }:
                return self.py_rng.randint(0, 1000)
            if name.endswith("_count") or name in {
                "view_count",
                "comment_count",
                "followers_count",
                "following_count",
                "status_count",
                "likes_count",
                "reblogs_count",
                "reply_count",
            }:
                return self.py_rng.randint(0, 5000)
            return self.py_rng.randint(1, 1000)
        if t in {"decimal", "float", "double", "real"} or name in {"lat", "long"}:
            if name == "lat":
                return round(self.py_rng.uniform(-55, 70), 6)
            if name == "long":
                return round(self.py_rng.uniform(-170, 170), 6)
            return round(self.py_rng.uniform(0, 10000), 4)

        # JSON columns are serialized JSON text to preserve the schema's single-column shape.
        if t == "json":
            json_value: Any
            if name in {"aliases", "sponsors", "2fa_backup_codes"}:
                json_value = [f"synthetic_{idx + 1}", f"sample_{idx + 1}"]
            elif name in {"entities"}:
                json_value = [] if idx % 3 else {"hashtags": [], "mentions": []}
            elif name in {"story", "media_json"}:
                json_value = {"kind": "synthetic", "sequence": idx + 1}
            elif name in {"metadata", "data", "meta"}:
                json_value = {"synthetic": True, "sequence": idx + 1, "source": "pixelfed_schema_generator"}
            else:
                json_value = {"synthetic": True, "sequence": idx + 1}
            return json.dumps(json_value, separators=(",", ":"), ensure_ascii=False)

        if name in {"email", "response"} and "email" in name:
            return f"{table}_{idx + 1:06d}@example.test"
        if name in {"username", "user_username"}:
            return f"{table}_user_{idx + 1:06d}"
        if name == "name":
            if table == "hashtags":
                return f"tag_{idx + 1:04d}"
            return self.fake.name()
        if name in {"first_name"}:
            return self.fake.first_name()
        if name in {"domain"}:
            if self.py_rng.random() < 0.8:
                return None if col.nullable else "pixelfed.example.test"
            return f"remote-{idx + 1:05d}.example.test"
        if name == "country":
            return self.py_rng.choice(
                ["Egypt", "United States", "United Kingdom", "Germany", "France", "Brazil", "Japan"]
            )
        if name == "language":
            return self.py_rng.choice(["en", "ar", "fr", "de", "es"])
        if name in {"status"}:
            return self.py_rng.choice(["active", "active", "pending", "suspended"])
        if name in {"visibility"}:
            return self.py_rng.choice(["public", "public", "unlisted", "private", "followers"])
        if name in {"scope"}:
            return self.py_rng.choice(["public", "public", "followers", "private"])
        if name in {"type", "item_type", "object_type", "filterable_type"}:
            options = {
                "statuses": ["photo", "video"],
                "stories": ["photo", "video"],
                "reports": ["spam", "abuse", "copyright", "other"],
                "collection_items": ["App\\Status", "App\\Collection"],
                "account_logs": ["App\\User", "App\\Status", "App\\Media", "App\\Profile"],
                "notifications": ["App\\Status", "App\\Like", "App\\Comment", "App\\Follower"],
                "direct_messages": ["App\\Status"],
            }
            return self.py_rng.choice(options.get(table, ["Create", "Like", "Follow", "Update"]))
        if name == "action":
            return self.py_rng.choice(["create", "update", "delete", "like", "comment", "follow", "login", "logout"])
        if name == "service":
            return self.py_rng.choice(["Instagram", "Flickr", "Mastodon", "Pixelfed", "Generic"])
        if name == "role":
            return self.py_rng.choice(["member", "admin", "moderator"])
        if name in {"queue"}:
            return self.py_rng.choice(["default", "media", "imports", "notifications"])
        if name == "connection":
            return self.py_rng.choice(["sync", "database", "redis"])
        if name == "mime":
            return self.py_rng.choice(["image/jpeg", "image/png", "video/mp4"])
        if name == "orientation":
            return self.py_rng.choice(["landscape", "portrait", "square"])
        if name == "filter_name":
            return self.py_rng.choice(["normal", "clarendon", "lark", "juno", "valencia"])
        if name == "license":
            return "CC-BY-4.0"
        if name in {"ip", "ip_address"}:
            return self.fake.ipv4_private()
        if name == "user_agent":
            return self.fake.user_agent()
        if name in {
            "website",
            "url",
            "link",
            "redirect",
            "admin_url",
            "remote_url",
            "cdn_url",
            "optimized_url",
            "thumbnail_url",
            "avatar_url",
            "header_photo_url",
            "sharedInbox",
            "inbox_url",
            "outbox_url",
            "follower_url",
            "following_url",
            "key_id",
        } or name.endswith("_url"):
            return f"https://example.test/{table}/{name}/{idx + 1:06d}"
        if name in {
            "password",
            "secret",
            "private_key",
            "public_key",
            "2fa_secret",
            "remember_token",
            "user_token",
            "random_token",
            "token",
            "key",
            "fingerprint",
            "original_sha256",
            "optimized_sha256",
        }:
            # Intentionally fake placeholders only; these are not usable credentials or keys.
            return hashlib.sha256(f"SYNTHETIC_ONLY|{self.seed}|{table}|{name}|{idx}".encode()).hexdigest()
        if name in {"payload", "media_json", "data"}:
            return json.dumps({"synthetic": True, "table": table, "sequence": idx + 1})
        if name in {
            "bio",
            "description",
            "comment",
            "message",
            "summary",
            "body",
            "body_rendered",
            "rendered",
            "caption",
            "exception",
            "response",
        }:
            if name == "exception":
                return "SyntheticExampleError: generated mock failure for pipeline testing"
            if name == "rendered" and table == "statuses":
                return "Synthetic rendered status text"
            if name == "caption" and table == "statuses":
                return self.fake.sentence(nb_words=10)
            return self.fake.sentence(nb_words=10)
        if name in {"title"}:
            return self.fake.sentence(nb_words=4).rstrip(".")
        if name == "slug":
            return f"{table.replace('_', '-')}-{idx + 1:06d}"
        if name in {"uri", "object_url"}:
            return f"https://pixelfed.example.test/{table}/{idx + 1:08d}"
        if name in {"item_type", "object_type"}:
            return "App\\Status"
        if name in {"uuid"}:
            return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.seed}/{table}/{idx}"))
        if name in {"path", "media_path", "thumbnail_path", "thumb_path", "hls_path", "storage_path", "root"}:
            return f"storage/{table}/{idx + 1:08d}.bin"
        if name == "template":
            return self.py_rng.choice(["default", "page", "article"])
        if name == "category":
            return self.py_rng.choice(["Community", "Product", "News", "Guidelines", "Updates"])
        if name == "app_id":
            return f"pixelfed-app-{idx + 1:04d}"
        if name in {"failed_at"}:
            return self._timestamp_value(table, name, idx)
        if t in {"varchar", "text", "longtext", "enum"}:
            return f"synthetic_{table}_{name}_{idx + 1:06d}"
        return f"synthetic_{table}_{name}_{idx + 1:06d}"

    def _generate_table(self, table_name: str) -> list[dict[str, Any]]:
        table = self.schema.tables[table_name]
        count = self.row_counts[table_name]
        rows: list[dict[str, Any]] = []
        for i in range(count):
            row: dict[str, Any] = {}
            for col in table.columns:
                if (table_name, col.name) in self.identity_values:
                    value = self.identity_values[(table_name, col.name)][i]
                else:
                    value = self._scalar_value(table_name, col, i)
                row[col.name] = value
            # The same deterministic persona is reused for the linked profile later.
            # Suffixes guarantee unique handles without using unrelated table-specific IDs.
            if table_name == "users":
                persona = self._stable_persona(f"local-user-{row['id']}")
                row["name"] = persona["name"]
                row["username"] = persona["username"]
                row["email"] = persona["email"]
            if table_name == "hashtags" and "name" in row:
                row["name"] = f"photo_tag_{i + 1:05d}"
            if table_name == "hashtags" and "slug" in row:
                row["slug"] = f"photo-tag-{i + 1:05d}"
            # Self-follow edges are not valid social relationships.
            if table_name == "followers" and row.get("profile_id") == row.get("following_id"):
                choices = self.identity_values.get(("profiles", "id"), [])
                alternatives = [v for v in choices if v != row.get("profile_id")]
                if alternatives:
                    row["following_id"] = self.py_rng.choice(alternatives)
            rows.append(row)
        self._enforce_composite_uniques(table_name, rows)
        return rows

    @staticmethod
    def _set_profile_urls(profile: dict[str, Any], host: str) -> None:
        username = str(profile.get("username") or "user")
        base = f"https://{host}/users/{username}"
        profile["inbox_url"] = f"{base}/inbox"
        profile["outbox_url"] = f"{base}/outbox"
        profile["key_id"] = f"{base}#main-key"
        profile["follower_url"] = f"{base}/followers"
        profile["following_url"] = f"{base}/following"
        profile["webfinger"] = f"@{username}@{host}"
        profile["avatar_url"] = f"https://{host}/storage/avatars/{username}.jpg"
        profile["sharedInbox"] = f"https://{host}/inbox" if profile.get("domain") else None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

    def _synchronize_entity_relationships(self) -> dict[str, int]:
        """Make cross-table identity attributes agree with their canonical entity rows.

        IDs remain table-scoped primary keys, as in relational databases. The stable identity
        rule is instead enforced through the correct FK: profiles.user_id -> users.id and
        users.profile_id -> profiles.id. Remote profiles intentionally have no local users row.
        """
        users = self.datasets.get("users", [])
        profiles = self.datasets.get("profiles", [])
        local_count = min(len(users), len(profiles))
        users_by_id = {row["id"]: row for row in users}
        profiles_by_id = {row["id"]: row for row in profiles}
        profiles_by_user_id: dict[Any, dict[str, Any]] = {}
        user_profile_pairs = 0

        # Pair local accounts and their profiles in a deterministic one-to-one map.
        for idx, profile in enumerate(profiles):
            if idx < local_count:
                user = users[idx]
                profile["user_id"] = user["id"]
                user["profile_id"] = profile["id"]
                profile["domain"] = None
                profile["username"] = user["username"]
                profile["name"] = user["name"]
                profile["status"] = user["status"]
                self._set_profile_urls(profile, "pixelfed.example.test")
                # Account/profile create/update dates should describe the same lifecycle.
                if user.get("created_at"):
                    profile["created_at"] = user["created_at"]
                if user.get("updated_at"):
                    profile["updated_at"] = max(
                        str(user.get("updated_at") or ""),
                        str(profile.get("updated_at") or ""),
                        key=lambda x: x,
                    ) or user.get("updated_at")
                profiles_by_user_id[user["id"]] = profile
                user_profile_pairs += 1
            else:
                # Federated profiles should use a host present in the synthetic instance dimension.
                profile["user_id"] = None
                remote_hosts = [
                    str(instance["domain"])
                    for instance in self.datasets.get("instances", [])
                    if instance.get("domain") and instance.get("domain") != "pixelfed.example.test"
                ]
                host_no = idx - local_count + 1
                profile["domain"] = (
                    remote_hosts[(host_no - 1) % len(remote_hosts)]
                    if remote_hosts
                    else f"node-{host_no:04d}.example.test"
                )
                remote_persona = self._stable_persona(f"remote-profile-{profile['id']}")
                profile["username"] = f"remote_{remote_persona['username']}"
                if not profile.get("name"):
                    profile["name"] = remote_persona["name"]
                profile["webfinger"] = f"@{profile['username']}@{profile['domain']}"
                self._set_profile_urls(profile, str(profile["domain"]))
        for user in users[local_count:]:
            user["profile_id"] = None

        # Row-level assignments that represent the same actor/account must agree.
        # Comments, media and reports store both the account and profile identity.
        for table_name in ("comments", "reports"):
            for row in self.datasets.get(table_name, []):
                profile = profiles_by_id.get(row.get("profile_id"))
                if profile is not None:
                    row["user_id"] = profile.get("user_id")

        statuses_by_id = {r["id"]: r for r in self.datasets.get("statuses", [])}
        for row in self.datasets.get("media", []):
            # A media record attached to a status belongs to the status author's profile.
            status = statuses_by_id.get(row.get("status_id"))
            if status is not None and status.get("profile_id") is not None:
                row["profile_id"] = status["profile_id"]
            profile = profiles_by_id.get(row.get("profile_id"))
            if profile is not None:
                row["user_id"] = profile.get("user_id")
                row["remote_media"] = int(profile.get("domain") is not None)
            elif row.get("profile_id") is None:
                row["user_id"] = None

        for row in self.datasets.get("status_hashtags", []):
            status = statuses_by_id.get(row.get("status_id"))
            if status is not None:
                row["profile_id"] = status.get("profile_id")
                row["status_visibility"] = status.get("visibility")

        # report_comments requires both user_id and profile_id, so keep them as the
        # same local actor. The reports FK remains independent from the commenting actor.
        for row in self.datasets.get("report_comments", []):
            user = users_by_id.get(row.get("user_id"))
            if user is not None and user.get("profile_id") is not None:
                row["profile_id"] = user["profile_id"]
            else:
                local_users = [u for u in users if u.get("profile_id") is not None]
                if local_users:
                    user = local_users[int(row["id"]) % len(local_users)]
                    row["user_id"] = user["id"]
                    row["profile_id"] = user["profile_id"]

        # Enforce chronology: an update/render/processing event cannot precede creation.
        chronology_fixes = 0
        for table_name, rows in self.datasets.items():
            for row in rows:
                created = self._parse_datetime(row.get("created_at"))
                if created is None:
                    continue
                for later_col in ("updated_at",):
                    later = self._parse_datetime(row.get(later_col))
                    if later is not None and later < created:
                        row[later_col] = created.isoformat(sep=" ")
                        chronology_fixes += 1
                for later_col in (
                    "processed_at",
                    "rendered_at",
                    "last_processed_at",
                    "last_fetched_at",
                    "hls_transcoded_at",
                    "responded_at",
                    "completed_at",
                ):
                    later = self._parse_datetime(row.get(later_col))
                    if later is not None and later < created:
                        row[later_col] = created.isoformat(sep=" ")
                        chronology_fixes += 1

        # Counters mirror generated event tables, not unrelated random numbers.
        statuses = self.datasets.get("statuses", [])
        likes = self.datasets.get("likes", [])
        followers = self.datasets.get("followers", [])
        like_counts: dict[Any, int] = defaultdict(int)
        reply_counts: dict[Any, int] = defaultdict(int)
        reblog_counts: dict[Any, int] = defaultdict(int)
        for like in likes:
            if like.get("status_id") is not None and like.get("deleted_at") is None:
                like_counts[like["status_id"]] += 1
        for status in statuses:
            if status.get("in_reply_to_id") is not None:
                reply_counts[status["in_reply_to_id"]] += 1
            if status.get("reblog_of_id") is not None:
                reblog_counts[status["reblog_of_id"]] += 1
        for status in statuses:
            status["likes_count"] = like_counts[status["id"]]
            status["reply_count"] = reply_counts[status["id"]]
            status["reblogs_count"] = reblog_counts[status["id"]]

        status_count_by_profile: dict[Any, int] = defaultdict(int)
        followers_by_profile: dict[Any, int] = defaultdict(int)
        following_by_profile: dict[Any, int] = defaultdict(int)
        for status in statuses:
            if status.get("profile_id") is not None:
                status_count_by_profile[status["profile_id"]] += 1
        for edge in followers:
            if edge.get("following_id") is not None:
                followers_by_profile[edge["following_id"]] += 1
            if edge.get("profile_id") is not None:
                following_by_profile[edge["profile_id"]] += 1
        for profile in profiles:
            profile["status_count"] = status_count_by_profile[profile["id"]]
            profile["followers_count"] = followers_by_profile[profile["id"]]
            profile["following_count"] = following_by_profile[profile["id"]]

        return {
            "local_user_profile_pairs": user_profile_pairs,
            "remote_profiles_without_users": max(0, len(profiles) - local_count),
            "identity_link_checks": user_profile_pairs * 2,
            "chronology_fixes": chronology_fixes,
        }

    def _fallback_value(self, table: str, col_name: str, row_index: int, attempt: int) -> Any:
        col = self.schema.tables[table].col(col_name)
        if (table, col_name) in self.references:
            candidates = self._target_values(table, col_name)
            if candidates:
                return self.py_rng.choice(candidates)
        if col.mysql_type in {"tinyint", "smallint", "int", "integer", "bigint"}:
            return 100_000_000 + row_index * 1000 + attempt
        if col.mysql_type in {"decimal", "float", "double", "real"}:
            return float(100_000 + row_index * 100 + attempt)
        if col.mysql_type in {"timestamp", "datetime"}:
            return (self.run_at - timedelta(seconds=row_index * 1000 + attempt + 1)).isoformat(sep=" ")
        if col.mysql_type == "json":
            return json.dumps({"synthetic_unique": f"{table}_{col_name}_{row_index}_{attempt}"})
        return f"synthetic_unique_{table}_{col_name}_{row_index}_{attempt}"

    def _enforce_composite_uniques(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        for idx_table, columns, is_unique, _index_name in self.unique_indexes:
            if idx_table != table_name or not is_unique:
                continue
            seen: set[tuple[Any, ...]] = set()
            for row_i, row in enumerate(rows):
                key = tuple(row[c] for c in columns)
                if any(v is None for v in key):
                    continue  # MySQL unique indexes permit multiple tuples containing NULL.
                attempt = 0
                while key in seen:
                    attempt += 1
                    if attempt > 10_000:
                        raise RuntimeError(f"Unable to satisfy unique index {table_name}({', '.join(columns)})")
                    mutable_cols = [
                        c
                        for c in reversed(columns)
                        if c not in self.unique_columns.get(table_name, set())
                        and not self.schema.tables[table_name].col(c).primary_key
                    ]
                    if mutable_cols:
                        # Prefer modifying a non-FK value (e.g. path, object_type, fingerprint).
                        non_ref = [c for c in mutable_cols if (table_name, c) not in self.references]
                        target_col = non_ref[0] if non_ref else mutable_cols[0]
                        if non_ref:
                            row[target_col] = self._fallback_value(table_name, target_col, row_i, attempt)
                        else:
                            row[target_col] = self._fallback_value(table_name, target_col, row_i, attempt)
                            # If still colliding, vary the other referenced components too.
                            for c in mutable_cols[1:]:
                                row[c] = self._fallback_value(table_name, c, row_i, attempt + 13)
                    else:
                        raise RuntimeError(f"All columns are immutable for unique index on {table_name}: {columns}")
                    # Avoid self-follow rows after modifying the composite pair.
                    if table_name == "followers" and row.get("profile_id") == row.get("following_id"):
                        alternatives = [
                            v for v in self.identity_values.get(("profiles", "id"), []) if v != row.get("profile_id")
                        ]
                        if alternatives:
                            row["following_id"] = self.py_rng.choice(alternatives)
                    key = tuple(row[c] for c in columns)
                    if any(v is None for v in key):
                        break
                if not any(v is None for v in key):
                    seen.add(key)

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        LOG.info("Generating %d schema tables at scale %.3f", len(self.schema.tables), self.scale)
        for index, table_name in enumerate(self.schema.tables, start=1):
            LOG.info(
                "[%02d/%02d] Generating %-36s %8s rows",
                index,
                len(self.schema.tables),
                table_name,
                f"{self.row_counts[table_name]:,}",
            )
            self.datasets[table_name] = self._generate_table(table_name)

        # Apply product-domain and business semantics before reconciling identities.
        from domain_realism import apply_domain_realism
        from business_enrichment import apply_business_enrichment

        self.domain_realism = apply_domain_realism(self)
        self.business_enrichment = apply_business_enrichment(self)
        self.identity_consistency = self._synchronize_entity_relationships()
        self._validate_datasets()
        return self.datasets

    def _validate_datasets(self) -> dict[str, Any]:
        errors: list[str] = []
        checks = 0
        table_results: dict[str, Any] = {}
        for table_name, table in self.schema.tables.items():
            rows = self.datasets[table_name]
            checks += 1
            if any(list(r.keys()) != table.column_names for r in rows):
                errors.append(f"{table_name}: output columns/order differ from schema")
            for col in table.columns:
                if not col.nullable or col.primary_key:
                    checks += 1
                    bad = sum(row.get(col.name) is None for row in rows)
                    if bad:
                        errors.append(f"{table_name}.{col.name}: {bad} NULL values but schema requires NOT NULL")
                if col.primary_key:
                    checks += 1
                    vals = [r[col.name] for r in rows]
                    if len(set(vals)) != len(vals):
                        errors.append(f"{table_name}.{col.name}: duplicate primary key")
                if col.unique and not col.primary_key:
                    checks += 1
                    vals = [r[col.name] for r in rows if r[col.name] is not None]
                    if len(set(vals)) != len(vals):
                        errors.append(f"{table_name}.{col.name}: duplicate unique value")
            for index_table, cols, is_unique, index_name in self.schema.indexes:
                if index_table != table_name or not is_unique:
                    continue
                if len(cols) == 1 and self.schema.tables[table_name].col(cols[0]).unique:
                    continue
                checks += 1
                seen: set[tuple[Any, ...]] = set()
                for r in rows:
                    key = tuple(r[c] for c in cols)
                    if any(v is None for v in key):
                        continue
                    if key in seen:
                        errors.append(f"{table_name}: duplicate tuple for unique index {index_name}")
                        break
                    seen.add(key)
            table_results[table_name] = {"row_count": len(rows), "column_count": len(table.columns)}

        # Validate every declared/inferred relationship used in the replica.
        for (child_table, child_col), (parent_table, parent_col) in self.references.items():
            if child_table not in self.datasets or parent_table not in self.datasets:
                continue
            parent_vals = {r[parent_col] for r in self.datasets[parent_table] if r[parent_col] is not None}
            child_def = self.schema.tables[child_table].col(child_col)
            missing = 0
            for row in self.datasets[child_table]:
                value = row[child_col]
                if value is None and child_def.nullable:
                    continue
                if value not in parent_vals:
                    missing += 1
            checks += 1
            if missing:
                errors.append(f"{child_table}.{child_col}: {missing} values do not match {parent_table}.{parent_col}")

        # Validate canonical account/profile identity and paired actor fields.
        users_by_id = {r["id"]: r for r in self.datasets.get("users", [])}
        profiles_by_id = {r["id"]: r for r in self.datasets.get("profiles", [])}
        statuses_by_id = {r["id"]: r for r in self.datasets.get("statuses", [])}
        for user in self.datasets.get("users", []):
            profile_id = user.get("profile_id")
            if profile_id is None:
                continue
            profile = profiles_by_id.get(profile_id)
            checks += 1
            if profile is None or profile.get("user_id") != user["id"]:
                errors.append(f"users.id={user['id']}: profile_id does not map back through profiles.user_id")
            elif profile.get("username") != user.get("username") or profile.get("name") != user.get("name"):
                errors.append(f"users.id={user['id']}: linked profile name/username does not match canonical account")
        for profile in self.datasets.get("profiles", []):
            user_id = profile.get("user_id")
            if user_id is None:
                continue  # Federated/remote profiles do not have a local users row.
            user = users_by_id.get(user_id)
            checks += 1
            if user is None or user.get("profile_id") != profile["id"]:
                errors.append(f"profiles.id={profile['id']}: user_id does not map back through users.profile_id")
        for table_name in ("comments", "media", "reports", "report_comments"):
            for row in self.datasets.get(table_name, []):
                profile = profiles_by_id.get(row.get("profile_id"))
                if profile is None:
                    continue
                expected_user = profile.get("user_id")
                checks += 1
                if row.get("user_id") != expected_user:
                    errors.append(f"{table_name}.id={row.get('id')}: user_id does not match profile_id owner")
        for table_name in ("media", "status_hashtags"):
            for row in self.datasets.get(table_name, []):
                status = statuses_by_id.get(row.get("status_id"))
                if status is None or status.get("profile_id") is None:
                    continue
                checks += 1
                if row.get("profile_id") != status.get("profile_id"):
                    errors.append(
                        f"{table_name}.id={row.get('id')}: profile_id does not match associated status author"
                    )
        from domain_realism import validate_domain_quality
        from business_enrichment import validate_business_enrichment

        domain_quality = validate_domain_quality(self)
        business_quality = validate_business_enrichment(self)
        checks += len(domain_quality["checks"]) + len(business_quality["checks"])
        errors.extend(domain_quality["errors"])
        errors.extend(business_quality["errors"])
        report = {
            "project": "PixelFed Schema-Exact Synthetic Lakehouse",
            "schema_file": "schema.md",
            "schema_table_count": len(self.schema.tables),
            "generated_table_count": len(self.datasets),
            "total_rows": sum(len(x) for x in self.datasets.values()),
            "scale": self.scale,
            "seed": self.seed,
            "as_of_utc": self.run_at.isoformat() + "Z",
            "checks_run": checks,
            "passed": not errors,
            "errors": errors,
            "identity_consistency": getattr(self, "identity_consistency", {}),
            "domain_realism": getattr(self, "domain_realism", {}),
            "business_enrichment": getattr(self, "business_enrichment", {}),
            "domain_quality": domain_quality,
            "business_quality": business_quality,
            "tables": table_results,
        }
        if errors:
            raise ValueError("Data-quality validation failed:\n - " + "\n - ".join(errors[:100]))
        return report

    def _format_row_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        if isinstance(value, datetime):
            return value.isoformat(sep=" ")
        return value

    def _write_csv(self, table_name: str, compressed: bool) -> Path:
        folder = self.output_dir / ("csv_gz" if compressed else "csv")
        folder.mkdir(parents=True, exist_ok=True)
        suffix = ".csv.gz" if compressed else ".csv"
        path = folder / f"{table_name}{suffix}"
        tmp = path.with_suffix(path.suffix + ".tmp")
        opener = gzip.open if compressed else open
        kwargs = {"mode": "wt", "encoding": "utf-8", "newline": ""}
        with opener(tmp, **kwargs) as stream:
            writer = csv.DictWriter(
                stream, fieldnames=self.schema.tables[table_name].column_names, extrasaction="raise"
            )
            writer.writeheader()
            for row in self.datasets[table_name]:
                writer.writerow({k: self._format_row_value(v) for k, v in row.items()})
        tmp.replace(path)
        return path

    def _pandas_frame(self, table_name: str):
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas is required for Parquet/Feather exports. Install requirements.txt") from exc
        frame = pd.DataFrame(self.datasets[table_name], columns=self.schema.tables[table_name].column_names)
        for col in self.schema.tables[table_name].columns:
            if col.mysql_type in {"tinyint", "smallint", "int", "integer", "bigint"}:
                # Nullable integer dtype preserves IDs and flags as integers when NULLs exist.
                try:
                    frame[col.name] = pd.array(frame[col.name], dtype="Int64")
                except (TypeError, ValueError):
                    pass
            elif col.mysql_type in {"timestamp", "datetime"}:
                frame[col.name] = pd.to_datetime(frame[col.name], errors="coerce")
            elif col.mysql_type in {"decimal", "float", "double", "real"}:
                frame[col.name] = pd.to_numeric(frame[col.name], errors="coerce")
            elif col.mysql_type in {"varchar", "text", "longtext", "json", "enum"}:
                frame[col.name] = frame[col.name].astype("string")
        return frame

    def _write_parquet(self, table_name: str) -> Path:
        try:
            import pyarrow  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("Parquet/Feather output requires pyarrow. Run: python -m pip install pyarrow") from exc
        folder = self.output_dir / "parquet"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{table_name}.parquet"
        tmp = folder / f"{table_name}.tmp.parquet"
        self._pandas_frame(table_name).to_parquet(tmp, engine="pyarrow", compression="snappy", index=False)
        tmp.replace(path)
        return path

    def _write_feather(self, table_name: str) -> Path:
        try:
            import pyarrow  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("Feather output requires pyarrow. Run: python -m pip install pyarrow") from exc
        folder = self.output_dir / "feather"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{table_name}.feather"
        tmp = folder / f"{table_name}.tmp.feather"
        self._pandas_frame(table_name).to_feather(tmp, compression="zstd")
        tmp.replace(path)
        return path

    def _write_jsonl(self, table_name: str) -> Path:
        folder = self.output_dir / "jsonl"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{table_name}.jsonl"
        tmp = folder / f"{table_name}.tmp.jsonl"
        with tmp.open("w", encoding="utf-8", newline="\n") as stream:
            for row in self.datasets[table_name]:
                clean = {k: self._format_row_value(v) for k, v in row.items()}
                stream.write(json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n")
        tmp.replace(path)
        return path

    def _sqlite_type(self, mysql_type: str) -> str:
        # Retain the documented type token. SQLite assigns compatible affinities to these labels.
        return mysql_type.upper()

    def _write_sqlite(self) -> Path:
        folder = self.output_dir / "sqlite"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "pixelfed_schema_replica.sqlite"
        tmp = folder / "pixelfed_schema_replica.tmp.sqlite"
        if tmp.exists():
            tmp.unlink()
        conn = sqlite3.connect(tmp)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            for table_name, table in self.schema.tables.items():
                col_defs: list[str] = []
                for col in table.columns:
                    definition = f"{_quote(col.name)} {self._sqlite_type(col.mysql_type)}"
                    if not col.nullable or col.primary_key:
                        definition += " NOT NULL"
                    if col.primary_key:
                        definition += " PRIMARY KEY"
                    if col.unique and not col.primary_key:
                        definition += " UNIQUE"
                    col_defs.append(definition)
                foreign_keys: list[tuple[str, str, str]] = []
                for (child_table, child_col), (parent_table, parent_col) in self.references.items():
                    if child_table == table_name:
                        item = (child_col, parent_table, parent_col)
                        if item not in foreign_keys:
                            foreign_keys.append(item)
                for child_col, parent_table, parent_col in foreign_keys:
                    col_defs.append(
                        f"FOREIGN KEY ({_quote(child_col)}) REFERENCES {_quote(parent_table)}({_quote(parent_col)}) DEFERRABLE INITIALLY DEFERRED"
                    )
                statement = f"CREATE TABLE {_quote(table_name)} ({', '.join(col_defs)})"
                conn.execute(statement)

            # Inline schema indexes.
            for table_name, table in self.schema.tables.items():
                for col in table.columns:
                    if col.indexed and not col.primary_key:
                        index_name = f"idx_{table_name}_{col.name}"
                        conn.execute(
                            f"CREATE INDEX IF NOT EXISTS {_quote(index_name)} ON {_quote(table_name)} ({_quote(col.name)})"
                        )
            for table_name, cols, is_unique, index_name in self.schema.indexes:
                unique_sql = "UNIQUE " if is_unique else ""
                quoted_cols = ", ".join(_quote(c) for c in cols)
                conn.execute(
                    f"CREATE {unique_sql}INDEX IF NOT EXISTS {_quote(index_name)} ON {_quote(table_name)} ({quoted_cols})"
                )

            conn.execute("BEGIN")
            conn.execute("PRAGMA defer_foreign_keys = ON")
            for table_name, table in self.schema.tables.items():
                columns = table.column_names
                placeholders = ",".join("?" for _ in columns)
                statement = f"INSERT INTO {_quote(table_name)} ({', '.join(_quote(c) for c in columns)}) VALUES ({placeholders})"
                tuples = [tuple(self._format_row_value(r[c]) for c in columns) for r in self.datasets[table_name]]
                conn.executemany(statement, tuples)
            conn.commit()
            # `foreign_key_check` is important because some source schema relationships are cyclic.
            fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
            if fk_errors:
                raise ValueError(f"SQLite foreign-key check failed ({len(fk_errors)} violations): {fk_errors[:10]}")
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise ValueError(f"SQLite integrity_check failed: {integrity}")
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        tmp.replace(path)
        return path

    def export(self, report: dict[str, Any], schema_path: Path) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        if "csv" in self.formats:
            for name in self.schema.tables:
                paths.append(str(self._write_csv(name, compressed=False).relative_to(self.output_dir)))
        if "csv_gz" in self.formats:
            for name in self.schema.tables:
                paths.append(str(self._write_csv(name, compressed=True).relative_to(self.output_dir)))
        if "parquet" in self.formats:
            for name in self.schema.tables:
                paths.append(str(self._write_parquet(name).relative_to(self.output_dir)))
        if "jsonl" in self.formats:
            for name in EVENT_TABLES:
                if name in self.datasets:
                    paths.append(str(self._write_jsonl(name).relative_to(self.output_dir)))
        if "feather" in self.formats:
            for name in FEATHER_TABLES:
                if name in self.datasets:
                    paths.append(str(self._write_feather(name).relative_to(self.output_dir)))
        if "sqlite" in self.formats:
            paths.append(str(self._write_sqlite().relative_to(self.output_dir)))

        metadata_dir = self.output_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(schema_path, metadata_dir / "schema.md")
        contract_json = {
            "database": "mysql",
            "table_count": len(self.schema.tables),
            "tables": {
                table_name: {
                    "columns": [
                        {
                            "name": c.name,
                            "mysql_type": c.mysql_type,
                            "nullable": c.nullable,
                            "primary_key": c.primary_key,
                            "unique": c.unique,
                            "indexed": c.indexed,
                            "foreign_key_marker": c.foreign_key_marker,
                        }
                        for c in table.columns
                    ]
                }
                for table_name, table in self.schema.tables.items()
            },
            "relationships": [
                {"child_table": ctab, "child_column": ccol, "parent_table": ptab, "parent_column": pcol}
                for (ctab, ccol), (ptab, pcol) in self.references.items()
            ],
            "unique_indexes": [
                {"table": table, "columns": list(cols), "name": name}
                for table, cols, unique, name in self.schema.indexes
                if unique
            ],
        }
        (metadata_dir / "schema_contract.json").write_text(json.dumps(contract_json, indent=2), encoding="utf-8")
        report["formats_exported"] = sorted(self.formats)
        report["output_files"] = paths
        (metadata_dir / "data_quality_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manifest = {
            "project": "PixelFed Schema-Exact Synthetic Lakehouse",
            "output_directory": str(self.output_dir),
            "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "source_schema": "metadata/schema.md",
            "table_count": len(self.schema.tables),
            "total_rows": sum(len(v) for v in self.datasets.values()),
            "seed": self.seed,
            "scale": self.scale,
            "as_of_utc": self.run_at.isoformat() + "Z",
            "formats": sorted(self.formats),
            "files": paths,
            "note": "All records are synthetic. Columns and ordering follow the supplied schema.md; data types are inferred by the schema labels.",
        }
        (metadata_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        with (metadata_dir / "row_counts.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["table_name", "row_count", "column_count"])
            for name, table in self.schema.tables.items():
                writer.writerow([name, len(self.datasets[name]), len(table.columns)])


def parse_as_of(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use ISO-8601, for example 2026-10-14T12:00:00Z") from exc
    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic data for all tables in the PixelFed MySQL schema.")
    parser.add_argument(
        "--schema", type=Path, default=Path(__file__).with_name("schema.md"), help="Path to the supplied schema.md"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(DEFAULT_OUTPUT), help=f"Output directory (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--scale", type=float, default=1.0, help="Scale all table row counts (default: 1.0; try 0.01 for a smoke test)"
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed for reproducible synthetic values (default: 42)")
    parser.add_argument(
        "--as-of", type=str, default=None, help="Fixed UTC reference time, ISO-8601, e.g. 2026-10-14T12:00:00Z"
    )
    parser.add_argument(
        "--formats", type=str, default=DEFAULT_FORMATS, help="Comma-separated: csv,csv_gz,parquet,jsonl,feather,sqlite"
    )
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s | %(levelname)s | %(message)s")
    try:
        schema_path = args.schema.resolve()
        schema = parse_schema(schema_path)
        formats = {part.strip().lower() for part in args.formats.split(",") if part.strip()}
        if "parquet" in formats or "feather" in formats:
            try:
                import pandas  # noqa: F401
                import pyarrow  # noqa: F401
            except ImportError:
                parser.error(
                    "Parquet/Feather exports require pandas and pyarrow. Install with: python -m pip install -r requirements.txt"
                )
        generator = SchemaDrivenGenerator(
            schema=schema,
            output_dir=args.output_dir,
            seed=args.seed,
            scale=args.scale,
            as_of=parse_as_of(args.as_of),
            formats=formats,
        )
        datasets = generator.generate()
        report = generator._validate_datasets()
        generator.export(report, schema_path)
        LOG.info("SUCCESS: generated all %d schema tables and %,d total rows", len(datasets), report["total_rows"])
        LOG.info("Output directory: %s", args.output_dir)
        LOG.info("Data-quality report: %s", args.output_dir / "metadata" / "data_quality_report.json")
        return 0
    except Exception as exc:
        LOG.exception("Generation failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(
        "This module is an internal generation engine. Run `python src/generate_landing.py` from the repository root."
    )
