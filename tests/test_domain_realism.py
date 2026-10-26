"""Domain quality and large-stream behavior tests."""

from __future__ import annotations

import csv
import gzip
import json
from datetime import date, datetime
from pathlib import Path

from generate_activity_stream import generate_stream
from schema_generator_core import SchemaDrivenGenerator, parse_as_of


def test_relational_generation_has_product_domain_semantics(parsed_schema, tmp_path: Path):
    """Schema-valid rows must also reconcile product metrics and event chronology."""
    generator = SchemaDrivenGenerator(
        schema=parsed_schema,
        output_dir=tmp_path / "relational",
        seed=73,
        scale=0.03,
        as_of=parse_as_of("2026-10-26T12:00:00Z"),
        formats=set(),
    )
    generator.generate()

    report = generator._validate_datasets()
    assert report["domain_quality"]["passed"] is True
    assert report["domain_realism"]["synthetic_only"] is True
    assert report["domain_realism"]["hot_profiles"] >= 1
    assert report["domain_quality"]["checks"]["posts_with_content"] == len(generator.datasets["statuses"])
    assert all(
        row["likes_count"] >= 0 and row["reply_count"] >= 0 and row["reblogs_count"] >= 0
        for row in generator.datasets["statuses"]
    )


def test_activity_stream_is_partitioned_reproducible_in_count_and_causally_linked(tmp_path: Path):
    """A practical stream smoke test checks count, cutoff, partitions and object references."""
    as_of = datetime(2026, 3, 18, 12, 0, 0)
    manifest = generate_stream(
        event_count=700,
        profile_count=80,
        start_date=date(2026, 1, 1),
        as_of=as_of,
        seed=19,
        output_dir=tmp_path / "stream",
    )

    events = []
    for partition in manifest["partitions"]:
        path = tmp_path / "stream" / partition["file"]
        assert path.is_file()
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            events.extend(json.loads(line) for line in stream)

    dimension_path = tmp_path / "stream" / manifest["profile_dimension"]["file"]
    with gzip.open(dimension_path, "rt", encoding="utf-8", newline="") as stream:
        dimension_rows = list(csv.DictReader(stream))
    joined_at = {
        int(row["profile_id"]): datetime.fromisoformat(row["created_at"].removesuffix("Z")) for row in dimension_rows
    }
    federated_ids = {int(row["profile_id"]) for row in dimension_rows if row["is_federated"] == "True"}

    assert len(dimension_rows) == 80
    assert manifest["profile_dimension"]["row_count"] == 80
    assert set(joined_at) == set(range(1, 81))
    assert len(events) == 700
    assert len({event["event_id"] for event in events}) == 700
    assert all(event["run_id"] == manifest["run_id"] for event in events)
    repeat_manifest = generate_stream(
        event_count=700,
        profile_count=80,
        start_date=date(2026, 1, 1),
        as_of=as_of,
        seed=19,
        output_dir=tmp_path / "stream_repeat",
    )
    assert repeat_manifest["run_id"] == manifest["run_id"]
    assert manifest["quality_report"]["passed"] is True
    assert manifest["quality_report"]["no_future_event_timestamps"] is True
    assert all(datetime.fromisoformat(event["event_timestamp"].removesuffix("Z")) <= as_of for event in events)
    for event in events:
        event_time = datetime.fromisoformat(event["event_timestamp"].removesuffix("Z"))
        assert event_time >= joined_at[event["actor_profile_id"]]
        if event["target_profile_id"] is not None:
            assert event_time >= joined_at[event["target_profile_id"]]
        if event["actor_profile_id"] in federated_ids:
            assert event["is_federated"] is True

    created_posts = {event["object_id"] for event in events if event["event_type"] == "post_created"}
    assert created_posts
    assert all(
        event["object_id"] in created_posts
        for event in events
        if event["event_type"]
        in {"post_viewed", "like_created", "comment_created", "share_created", "report_created", "media_processed"}
    )
    created_stories = {event["object_id"] for event in events if event["event_type"] == "story_created"}
    assert all(event["object_id"] in created_stories for event in events if event["event_type"] == "story_viewed")
