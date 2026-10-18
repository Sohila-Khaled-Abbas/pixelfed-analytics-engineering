"""Tests for synthetic data generator determinism and referential integrity."""
from __future__ import annotations

from pathlib import Path
import pytest
from schema_generator_core import SchemaDrivenGenerator, parse_as_of, SchemaContract


def test_generator_determinism(parsed_schema: SchemaContract, tmp_path: Path):
    """Running generator twice with identical seed produces identical primary keys."""
    as_of = parse_as_of("2026-10-14T12:00:00Z")
    gen1 = SchemaDrivenGenerator(
        schema=parsed_schema,
        output_dir=tmp_path / "run1",
        seed=123,
        scale=0.03,
        as_of=as_of,
        formats=set()
    )
    gen1.generate()

    gen2 = SchemaDrivenGenerator(
        schema=parsed_schema,
        output_dir=tmp_path / "run2",
        seed=123,
        scale=0.03,
        as_of=as_of,
        formats=set()
    )
    gen2.generate()

    # Compare generated user IDs and statuses
    users1 = [r["id"] for r in gen1.datasets["users"]]
    users2 = [r["id"] for r in gen2.datasets["users"]]
    assert users1 == users2, "User IDs must match across deterministic runs"

    status_ids1 = [r["id"] for r in gen1.datasets["statuses"]]
    status_ids2 = [r["id"] for r in gen2.datasets["statuses"]]
    assert status_ids1 == status_ids2, "Status IDs must match across deterministic runs"


def test_referential_integrity(parsed_schema: SchemaContract, tmp_path: Path):
    """Foreign keys in core child tables must exist in parent tables."""
    as_of = parse_as_of("2026-10-14T12:00:00Z")
    gen = SchemaDrivenGenerator(
        schema=parsed_schema,
        output_dir=tmp_path / "ri_test",
        seed=42,
        scale=0.03,
        as_of=as_of,
        formats=set()
    )
    gen.generate()

    user_ids = {r["id"] for r in gen.datasets["users"]}
    profile_ids = {r["id"] for r in gen.datasets["profiles"]}
    status_ids = {r["id"] for r in gen.datasets["statuses"]}

    # Profiles user_id
    for profile in gen.datasets["profiles"]:
        if profile.get("user_id") is not None:
            assert profile["user_id"] in user_ids, f"Profile {profile['id']} has orphaned user_id {profile['user_id']}"

    # Statuses profile_id (can be nullable in schema for remote federated posts)
    for status in gen.datasets["statuses"]:
        if status.get("profile_id") is not None:
            assert status["profile_id"] in profile_ids, f"Status {status['id']} has orphaned profile_id {status['profile_id']}"

    # Likes status_id and profile_id
    for like in gen.datasets["likes"]:
        if like.get("status_id") is not None:
            assert like["status_id"] in status_ids, f"Like {like['id']} has orphaned status_id {like['status_id']}"
        if like.get("profile_id") is not None:
            assert like["profile_id"] in profile_ids, f"Like {like['id']} has orphaned profile_id {like['profile_id']}"
