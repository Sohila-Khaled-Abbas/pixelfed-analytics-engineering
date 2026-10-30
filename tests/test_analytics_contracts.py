"""Regression tests for cross-format identity and the core engagement galaxy."""

from __future__ import annotations

import copy
import random
from datetime import datetime, timezone
from pathlib import Path

import pytest

from build_analytics import build_galaxy, clean_tables, parse_timestamp, validate_galaxy
from domain_realism import _sample_time
from landing_contracts import key, validate_records
from raw_quality import inject_raw_quality_issues
from schema_generator_core import SchemaDrivenGenerator, parse_as_of


@pytest.fixture
def generated(parsed_schema, tmp_path):
    gen = SchemaDrivenGenerator(
        schema=parsed_schema,
        output_dir=tmp_path,
        seed=42,
        scale=0.03,
        as_of=parse_as_of("2026-10-29T21:00:00Z"),
        formats=set(),
    )
    gen.generate()
    return gen


def test_detects_wrong_but_existing_user_id(generated):
    data = copy.deepcopy(generated.datasets)
    comment = next(row for row in data["comments"] if row["user_id"] is not None)
    comment["user_id"] = next(row["id"] for row in data["users"] if row["id"] != comment["user_id"])
    assert any("actor identity mismatch" in error for error in validate_records(data, generated.schema))


def test_exact_bigint_and_unsafe_float():
    assert key(9007199254740993) == "9007199254740993"
    assert key("9007199254740993") == "9007199254740993"
    with pytest.raises(ValueError, match="Unsafe"):
        key(float(9007199254740993))


def test_silver_nulls_no_key_changes_and_galaxy_reconciliation(generated):
    inject_raw_quality_issues(generated)
    silver, rejected = clean_tables(generated.datasets, generated.schema, generated.run_at.replace(tzinfo=timezone.utc))
    assert rejected == []
    for table, rows in silver.items():
        assert (
            [r["id"] for r in rows] == [r["id"] for r in generated.datasets[table]]
            if rows and "id" in rows[0]
            else True
        )
    assert any(row["bio"] is None for row in silver["profiles"])
    assert all(row["comment"] is None or row["comment"] == row["comment"].strip() for row in silver["comments"])
    gold = build_galaxy(silver)
    assert len(gold["fct_post"]) == len(silver["statuses"])
    assert len(gold["fct_comment"]) == len(silver["comments"])
    assert len(gold["dim_time"]) == 1440
    assert all(r["user_key"] == "0" for r in gold["dim_profile"] if r["is_local"] is False)
    weights = {}
    for row in gold["bridge_post_hashtag"]:
        weights[row["post_key"]] = weights.get(row["post_key"], 0) + row["allocation_weight"]
    assert all(abs(weight - 1) < 1e-9 for weight in weights.values())
    gold["fct_like"][0]["profile_key"] = "missing-profile"
    with pytest.raises(ValueError, match="orphan"):
        validate_galaxy(gold)


def test_quarantine_bad_timestamp_and_dependent_events(generated):
    data = copy.deepcopy(generated.datasets)
    post = data["statuses"][0]
    post["created_at"] = "not-a-date"
    silver, rejected = clean_tables(data, generated.schema, generated.run_at.replace(tzinfo=timezone.utc))
    assert any("invalid_timestamp:created_at" in row["reasons"] for row in rejected)
    assert post["id"] not in {r["id"] for r in silver["statuses"]}
    assert all(r["status_id"] != post["id"] for r in silver["likes"])
    assert sum(map(len, data.values())) == sum(map(len, silver.values())) + len(rejected)
    build_galaxy(silver)


def test_cairo_clock_utc_conversion_and_weekend(generated):
    assert parse_timestamp("2026-07-01T23:30:00+03:00").hour == 20
    assert parse_timestamp("2026/07/01 20:30:00").hour == 20
    silver, _ = clean_tables(generated.datasets, generated.schema, generated.run_at.replace(tzinfo=timezone.utc))
    gold = build_galaxy(silver)
    assert all(row["is_weekend"] == (row["weekday_iso"] in (5, 6)) for row in gold["dim_date"])
    rng = random.Random(23)
    start, end = datetime(2026, 4, 23), datetime(2026, 4, 25)
    assert all(start <= _sample_time(rng, start, end) <= end for _ in range(200))


def test_exported_identity_tampering_is_rejected(generated, tmp_path: Path):
    import csv
    import gzip

    from generate_landing import build_table_format_map, export_mixed
    from validate_landing import validate_landing

    landing = tmp_path / "exports"
    generated.output_dir = landing
    assignment = build_table_format_map(generated.schema)
    report = generated._validate_datasets()
    report["raw_quality"] = inject_raw_quality_issues(generated)
    export_mixed(generated, assignment, report, Path(__file__).parents[1] / "schema.md")
    assert validate_landing(landing, Path(__file__).parents[1] / "schema.md") == 0
    path = landing / "csv_gz/comments.csv.gz"
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames
        rows = list(reader)
    row = next(r for r in rows if r["user_id"])
    row["user_id"] = next(str(r["id"]) for r in generated.datasets["users"] if str(r["id"]) != row["user_id"])
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    # File shape and row counts still agree: this must fail on actor semantics.
    assert validate_landing(landing, Path(__file__).parents[1] / "schema.md") == 1


def test_event_cannot_precede_actor_registration(generated):
    from landing_contracts import validate_event_chronology

    assert validate_event_chronology(generated.datasets, generated.run_at) == []
    row = generated.datasets["likes"][0]
    row["created_at"] = "1900-01-01T00:00:00Z"
    assert any("event before actor or target creation" in e for e in validate_event_chronology(generated.datasets))


def test_comment_noise_targets_actual_schema_column(generated):
    before = [r["comment"] for r in generated.datasets["comments"]]
    inject_raw_quality_issues(generated)
    after = [r["comment"] for r in generated.datasets["comments"]]
    assert before != after
    assert any(value is None for value in after)
    assert all("reply" not in row for row in generated.datasets["comments"])


def test_xlsx_reader_preserves_omitted_trailing_null_cells(tmp_path):
    from openpyxl import Workbook

    from landing_contracts import read_tables

    book = Workbook(write_only=True)
    sheet = book.create_sheet("places")
    sheet.append(["id", "name", "lat", "long"])
    sheet.append([1, "Unverified area", None, None])
    path = tmp_path / "places.xlsx"
    book.save(path)
    rows = read_tables(tmp_path, {"places": {"format": "xlsx", "file": "places.xlsx"}})["places"]
    assert rows == [{"id": 1, "name": "Unverified area", "lat": None, "long": None}]
