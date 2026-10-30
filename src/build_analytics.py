#!/usr/bin/env python3
"""Build an auditable Silver layer and core engagement galaxy from native landing exports.

Strict source keys are never imputed. Bad event timestamps are quarantined, and
children of quarantined posts/stories are quarantined too. Outputs are new directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from landing_contracts import key, parse_timestamp, read_tables, validate_records
from schema_generator_core import parse_schema
from validate_landing import validate_landing

ROOT = Path(__file__).resolve().parents[1]
CAIRO = ZoneInfo("Africa/Cairo")
EVENTS = ("statuses", "likes", "comments", "followers", "media", "stories", "story_views", "bookmarks")


def clean_tables(data, schema, as_of):
    """Keep optional text NULL, trim text, normalize dates, quarantine invalid records."""
    silver, rejected = {}, []
    refs = {
        "statuses": ("profile_id",),
        "likes": ("profile_id", "status_id"),
        "comments": ("profile_id", "status_id"),
        "followers": ("profile_id", "following_id"),
        "media": ("profile_id",),
        "stories": ("profile_id",),
        "story_views": ("profile_id", "story_id"),
        "bookmarks": ("profile_id", "status_id"),
    }
    for table, rows in data.items():
        silver[table] = []
        for row in rows:
            clean = dict(row)
            reasons = []
            for col in schema.tables[table].columns:
                value = row.get(col.name)
                if value == "" and col.nullable:
                    value = None
                kind = col.mysql_type.lower()
                if kind.startswith(("timestamp", "datetime")):
                    try:
                        parsed = parse_timestamp(value)
                        clean[col.name] = parsed.isoformat().replace("+00:00", "Z") if parsed else None
                    except (ValueError, TypeError):
                        reasons.append(f"invalid_timestamp:{col.name}")
                elif kind.startswith(("varchar", "text", "longtext", "mediumtext", "char")):
                    # IDs and FK values are copied verbatim, including varchar IDs.
                    if col.primary_key or col.foreign_key_marker:
                        continue
                    clean[col.name] = str(value).strip() if value is not None else None
                    if clean[col.name] == "" and col.nullable:
                        clean[col.name] = None
            if table in EVENTS:
                try:
                    created = parse_timestamp(clean.get("created_at"))
                    if created is None:
                        reasons.append("missing_event_timestamp")
                    elif created > as_of:
                        reasons.append("event_after_cutoff")
                except ValueError:
                    pass  # already recorded above
                for col in refs[table]:
                    if key(clean.get(col)) is None:
                        reasons.append(f"missing_event_identity:{col}")
            if reasons:
                rejected.append({"table": table, "source_id": key(row.get("id")), "reasons": reasons, "row": row})
            else:
                silver[table].append(clean)
    # Dependency closure prevents orphan Gold facts after timestamp quarantine.
    for child, parent, fk in (
        ("media", "statuses", "status_id"),
        ("likes", "statuses", "status_id"),
        ("comments", "statuses", "status_id"),
        ("bookmarks", "statuses", "status_id"),
        ("status_hashtags", "statuses", "status_id"),
        ("story_views", "stories", "story_id"),
    ):
        valid = {key(r["id"]) for r in silver[parent]}
        kept = []
        for row in silver[child]:
            if key(row.get(fk)) is not None and key(row[fk]) not in valid:
                rejected.append(
                    {
                        "table": child,
                        "source_id": key(row.get("id")),
                        "reasons": [f"quarantined_parent:{parent}"],
                        "row": row,
                    }
                )
            else:
                kept.append(row)
        silver[child] = kept
    return silver, rejected


def build_galaxy(silver):
    """Use source PKs as deterministic keys in this single-source Type-1 model."""
    gold = {}
    profiles = {key(r["id"]): r for r in silver["profiles"]}
    posts = {key(r["id"]): r for r in silver["statuses"]}
    stories = {key(r["id"]): r for r in silver["stories"]}
    # All table-scoped IDs are exact text. 0 is reserved for unknown/not applicable.
    gold["dim_user"] = [{"user_key": "0", "user_id": None}] + [
        {"user_key": key(r["id"]), "user_id": key(r["id"]), "language": r.get("language")} for r in silver["users"]
    ]
    gold["dim_profile"] = [{"profile_key": "0", "profile_id": None, "is_local": None, "user_key": "0"}] + [
        {
            "profile_key": pid,
            "profile_id": pid,
            "user_key": key(r.get("user_id")) or "0",
            "is_local": key(r.get("user_id")) is not None,
            "username": r.get("username"),
            "bio": r.get("bio"),
            "bio_missing": r.get("bio") is None,
            "location": r.get("location"),
            "location_disclosed": r.get("location") is not None,
            "website_present": r.get("website") is not None,
        }
        for pid, r in profiles.items()
    ]
    gold["dim_place"] = [{"place_key": "0", "name": None, "country": None}] + [
        {
            "place_key": key(r["id"]),
            "name": r.get("name"),
            "country": r.get("country"),
            "latitude": r.get("lat"),
            "longitude": r.get("long"),
            "coordinate_missing": r.get("lat") in (None, "") or r.get("long") in (None, ""),
        }
        for r in silver["places"]
    ]
    gold["dim_post"] = [
        {
            "post_key": pid,
            "status_id": pid,
            "language": r.get("language"),
            "scope": r.get("scope"),
            "type": r.get("type"),
            "caption": r.get("caption"),
            "caption_missing": r.get("caption") is None,
            "is_reply": key(r.get("in_reply_to_id")) is not None,
            "is_reblog": key(r.get("reblog_of_id")) is not None,
            "is_deleted": r.get("deleted_at") is not None,
        }
        for pid, r in posts.items()
    ]
    gold["dim_hashtag"] = [{"hashtag_key": key(r["id"]), "name": r["name"]} for r in silver["hashtags"]]
    gold["dim_story"] = [
        {"story_key": sid, "story_id": sid, "author_profile_key": key(r["profile_id"])} for sid, r in stories.items()
    ]
    dates, minutes = {}, {}

    def clock(row):
        utc = parse_timestamp(row["created_at"])
        local = utc.astimezone(CAIRO)
        date_key = local.strftime("%Y%m%d")
        time_key = local.hour * 60 + local.minute
        dates[date_key] = {
            "date_key": date_key,
            "date": local.date().isoformat(),
            "weekday_iso": local.isoweekday(),
            "is_weekend": local.weekday() in (4, 5),
        }
        minutes[time_key] = {"time_key": time_key, "hour": local.hour, "minute": local.minute}
        return {
            "date_key": date_key,
            "time_key": time_key,
            "created_at_utc": utc.isoformat(),
            "created_at_cairo": local.isoformat(),
        }

    spec = {
        "statuses": "fct_post",
        "likes": "fct_like",
        "comments": "fct_comment",
        "followers": "fct_follow",
        "media": "fct_media",
        "stories": "fct_story",
        "story_views": "fct_story_view",
        "bookmarks": "fct_bookmark",
    }
    for source, target in spec.items():
        gold[target] = []
        for row in silver[source]:
            fact = {
                "source_id": key(row["id"]),
                "profile_key": key(row.get("profile_id")) or "0",
                "event_count": 1,
                **clock(row),
            }
            post_id = key(row.get("status_id"))
            if source == "statuses":
                fact["post_key"] = key(row["id"])
                fact["place_key"] = key(row.get("place_id")) or "0"
            elif source in {"likes", "comments", "media", "bookmarks"}:
                fact["post_key"] = post_id
                fact["author_profile_key"] = key(posts.get(post_id, {}).get("profile_id")) or "0"
            if source == "followers":
                fact["following_profile_key"] = key(row["following_id"])
            if source in {"stories", "story_views"}:
                sid = key(row["id"] if source == "stories" else row["story_id"])
                fact["story_key"] = sid
                fact["author_profile_key"] = key(stories[sid]["profile_id"])
            if source == "media":
                fact["mime_type"] = row.get("mime")
                for source_col, target_col in (("size", "file_size_bytes"), ("width", "width"), ("height", "height")):
                    value = row.get(source_col)
                    fact[target_col] = int(value) if value not in (None, "") else None
            if source == "comments":
                fact["is_deleted"] = row.get("deleted_at") is not None
                fact["comment_missing"] = row.get("comment") is None
                fact["character_length"] = len(row["comment"]) if row.get("comment") is not None else None
            if source == "likes":
                fact["is_deleted"] = row.get("deleted_at") is not None
            gold[target].append(fact)
    # Use a full date span to support time intelligence, including zero-activity days.
    from datetime import timedelta

    if dates:
        start = datetime.strptime(min(dates), "%Y%m%d").date()
        end = datetime.strptime(max(dates), "%Y%m%d").date()
        while start <= end:
            dates[start.strftime("%Y%m%d")] = {
                "date_key": start.strftime("%Y%m%d"),
                "date": start.isoformat(),
                "weekday_iso": start.isoweekday(),
                "is_weekend": start.weekday() in (4, 5),
            }
            start += timedelta(days=1)
    gold["dim_date"] = [dates[k] for k in sorted(dates)]
    gold["dim_time"] = [{"time_key": m, "hour": m // 60, "minute": m % 60} for m in range(1440)]
    pairs = sorted({(key(r["status_id"]), key(r["hashtag_id"])) for r in silver["status_hashtags"]})
    counts = Counter(pid for pid, _ in pairs)
    gold["bridge_post_hashtag"] = [
        {"post_key": pid, "hashtag_key": hid, "allocation_weight": 1 / counts[pid]} for pid, hid in pairs
    ]
    validate_galaxy(gold)
    return gold


def validate_galaxy(gold):
    """Fail on duplicate grains or orphan conformed/role-playing dimension keys."""
    dimensions = {
        "profile_key": ("dim_profile", "profile_key"),
        "author_profile_key": ("dim_profile", "profile_key"),
        "following_profile_key": ("dim_profile", "profile_key"),
        "post_key": ("dim_post", "post_key"),
        "date_key": ("dim_date", "date_key"),
        "time_key": ("dim_time", "time_key"),
        "hashtag_key": ("dim_hashtag", "hashtag_key"),
        "story_key": ("dim_story", "story_key"),
        "user_key": ("dim_user", "user_key"),
        "place_key": ("dim_place", "place_key"),
    }
    lookup = {col: {row[target] for row in gold[table]} for col, (table, target) in dimensions.items()}
    for table, target in set(dimensions.values()):
        keys = [r[target] for r in gold[table]]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{table}: duplicate dimension grain")
    pairs = [(r["post_key"], r["hashtag_key"]) for r in gold["bridge_post_hashtag"]]
    if len(pairs) != len(set(pairs)):
        raise ValueError("Duplicate post/hashtag bridge grain")
    totals = Counter()
    for row in gold["bridge_post_hashtag"]:
        totals[row["post_key"]] += row["allocation_weight"]
    if any(abs(v - 1) > 1e-9 for v in totals.values()):
        raise ValueError("Post/hashtag allocation weights must sum to one per tagged post")
    for table, rows in gold.items():
        if table.startswith("fct_"):
            ids = [row["source_id"] for row in rows]
            if len(ids) != len(set(ids)):
                raise ValueError(f"{table}: duplicate fact grain")
        for row in rows:
            for col, value in row.items():
                if col in lookup and value is not None and value not in lookup[col]:
                    raise ValueError(f"{table}.{col}: orphan {value}")


def build(landing: Path, output: Path, schema_path: Path):
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    if validate_landing(landing, schema_path):
        raise ValueError("Landing validation failed; no analytics output created")
    schema = parse_schema(schema_path)
    manifest_bytes = (landing / "metadata/manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    data = read_tables(landing, manifest["table_storage"])
    errors = validate_records(data, schema)
    if errors:
        raise ValueError("\n".join(errors[:30]))
    as_of = parse_timestamp(manifest["as_of_utc"])
    silver, rejected = clean_tables(data, schema, as_of)
    gold = build_galaxy(silver)
    report = {
        "synthetic_only": True,
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "as_of_utc": manifest["as_of_utc"],
        "timezone": "Africa/Cairo",
        "dimension_policy": "Type 1, single source",
        "source_rows": sum(map(len, data.values())),
        "silver_rows": sum(map(len, silver.values())),
        "quarantined_rows": len(rejected),
        "gold_rows": {k: len(v) for k, v in gold.items()},
        "passed": True,
        "scope": "core engagement galaxy; remaining Silver tables are staging only",
    }
    assert report["source_rows"] == report["silver_rows"] + report["quarantined_rows"]
    output.mkdir(parents=True)
    for layer, tables in (("silver", silver), ("gold", gold), ("audit", {"quarantine": rejected})):
        folder = output / layer
        folder.mkdir()
        for table, rows in tables.items():
            (folder / f"{table}.jsonl").write_text(
                "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows), encoding="utf-8"
            )
    (output / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landing", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=ROOT / "schema.md")
    args = parser.parse_args()
    print(json.dumps(build(args.landing, args.output, args.schema), indent=2))


if __name__ == "__main__":
    main()
