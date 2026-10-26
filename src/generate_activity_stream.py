#!/usr/bin/env python3
"""Stream a realistic, partitioned synthetic PixelFed activity lake without loading it all in memory.

Outputs one compressed JSONL file per calendar month plus a reproducibility and quality manifest.
All identities, activity, content labels, and operational metadata are fictional.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVENT_TYPES = [
    "post_created",
    "post_viewed",
    "like_created",
    "comment_created",
    "follow_created",
    "story_created",
    "story_viewed",
    "share_created",
    "search_performed",
    "report_created",
    "media_processed",
]
EVENT_WEIGHTS = [5.5, 48.0, 18.0, 7.0, 6.5, 1.6, 5.0, 3.8, 2.2, 0.25, 2.15]
VISIBILITIES = ["public", "unlisted", "followers", "private"]
VISIBILITY_WEIGHTS = [0.82, 0.08, 0.07, 0.03]
SOURCE_APPS = ["web", "android", "ios", "api", "federation_worker"]
SOURCE_WEIGHTS = [0.38, 0.23, 0.17, 0.08, 0.14]
HOUR_WEIGHTS = [
    0.25,
    0.15,
    0.10,
    0.08,
    0.08,
    0.10,
    0.18,
    0.35,
    0.60,
    0.85,
    1.0,
    1.05,
    1.0,
    0.95,
    0.95,
    1.05,
    1.25,
    1.45,
    1.55,
    1.45,
    1.25,
    0.95,
    0.65,
    0.40,
]


def _parse_as_of(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _months(start: date, end: date) -> list[tuple[date, date]]:
    cursor = date(start.year, start.month, 1)
    result: list[tuple[date, date]] = []
    while cursor <= end:
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)
        lower = max(start, cursor)
        upper = min(end, next_month - timedelta(days=1))
        if lower <= upper:
            result.append((lower, upper))
        cursor = next_month
    return result


def _allocate_monthly_counts(event_count: int, months: list[tuple[date, date]]) -> list[int]:
    weights = []
    for lower, upper in months:
        days = (upper - lower).days + 1
        # Seasonal volume is modest; weekends and late-month product campaigns create variation.
        month_factor = 1.0 + 0.12 * (lower.month in {3, 6, 9, 12}) + 0.08 * (lower.month in {7, 8})
        weights.append(days * month_factor)
    total = sum(weights)
    raw = [event_count * weight / total for weight in weights]
    counts = [int(value) for value in raw]
    remainder = event_count - sum(counts)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - counts[i], reverse=True)
    for idx in order[:remainder]:
        counts[idx] += 1
    return counts


def _sample_event_time(
    rng: random.Random, candidate_days: list[date], day_weights: list[float], as_of: datetime
) -> datetime:
    day = rng.choices(candidate_days, weights=day_weights, k=1)[0]
    hour = rng.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
    minute = rng.randrange(60)
    return min(as_of, datetime.combine(day, time(hour, minute, rng.randrange(60))))


def _actor_id(rng: random.Random, profile_count: int, hot_profiles: list[int]) -> int:
    # A small creator cohort receives a disproportionate amount of interaction.
    if hot_profiles and rng.random() < 0.22:
        return rng.choice(hot_profiles)
    return rng.randint(1, profile_count)


def _pick_post(rng: random.Random, posts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not posts:
        return None
    if rng.random() < 0.68:
        recent_start = max(0, len(posts) - 5000)
        return posts[rng.randrange(recent_start, len(posts))]
    return posts[rng.randrange(len(posts))]


def _properties(rng: random.Random, event_type: str) -> dict[str, Any]:
    if event_type == "post_created":
        return {
            "media_type": rng.choices(["photo", "video", "text"], [0.69, 0.20, 0.11], k=1)[0],
            "has_alt_text": rng.random() < 0.61,
            "has_content_warning": rng.random() < 0.07,
        }
    if event_type == "post_viewed":
        return {
            "surface": rng.choices(
                ["home_feed", "profile", "hashtag", "federated_feed", "explore"], [0.48, 0.16, 0.15, 0.13, 0.08], k=1
            )[0],
            "dwell_ms": int(min(120000, rng.lognormvariate(7.5, 0.85))),
        }
    if event_type == "like_created":
        return {"client_action": "like", "is_undo": rng.random() < 0.018}
    if event_type == "comment_created":
        return {
            "comment_length_bucket": rng.choices(["1-20", "21-80", "81-240", "241+"], [0.21, 0.48, 0.25, 0.06], k=1)[0],
            "contains_mention": rng.random() < 0.09,
        }
    if event_type == "follow_created":
        return {
            "relationship_type": "follow",
            "discovery_source": rng.choice(["profile", "suggestion", "hashtag", "reply"]),
        }
    if event_type in {"story_created", "story_viewed"}:
        return {
            "media_type": rng.choices(["photo", "video"], [0.82, 0.18], k=1)[0],
            "view_position": rng.randint(1, 20) if event_type == "story_viewed" else None,
        }
    if event_type == "search_performed":
        return {
            "query_category": rng.choice(["photography", "place", "creator", "hashtag", "topic"]),
            "result_count_bucket": rng.choice(["0", "1-5", "6-20", "21+"]),
        }
    if event_type == "report_created":
        return {
            "report_category": rng.choices(
                ["spam", "harassment", "copyright", "impersonation", "other"], [0.48, 0.20, 0.10, 0.08, 0.14], k=1
            )[0]
        }
    if event_type == "media_processed":
        return {
            "processing_ms": int(min(900000, rng.lognormvariate(9.2, 0.9))),
            "rendition": rng.choice(["thumbnail", "optimized", "hls", "metadata"]),
        }
    if event_type == "share_created":
        return {"share_surface": rng.choice(["profile", "direct_message", "external_link"])}
    return {}


def generate_stream(
    event_count: int, profile_count: int, start_date: date, as_of: datetime, seed: int, output_dir: Path
) -> dict[str, Any]:
    if event_count < 1:
        raise ValueError("--events must be at least 1")
    if profile_count < 2:
        raise ValueError("--profiles must be at least 2")
    start_at = datetime.combine(start_date, time.min)
    if as_of < start_at:
        raise ValueError("--as-of must not be earlier than --start-date")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Remove only outputs owned by this generator so reruns cannot leave stale monthly partitions.
    for partition_file in output_dir.glob("event_month=????-??/events.jsonl.gz"):
        partition_file.unlink()
        try:
            partition_file.parent.rmdir()
        except OSError:
            pass
    for metadata_name in ("manifest.json", "quality_report.json"):
        metadata_path = output_dir / metadata_name
        if metadata_path.is_file():
            metadata_path.unlink()

    rng = random.Random(seed)
    run_id = hashlib.sha256(
        f"{seed}|{start_date.isoformat()}|{as_of.isoformat()}|{profile_count}|{event_count}".encode()
    ).hexdigest()[:12]
    months = _months(start_date, as_of.date())
    month_counts = _allocate_monthly_counts(event_count, months)
    hot_count = max(1, profile_count // 100)
    hot_profiles = rng.sample(range(1, profile_count + 1), min(hot_count, profile_count))
    post_pool: list[dict[str, Any]] = []
    active_stories: list[dict[str, Any]] = []
    next_post_id = 1
    next_story_id = 1
    event_id = 0
    all_types: Counter[str] = Counter()
    partition_metadata: list[dict[str, Any]] = []
    distinct_actors: set[int] = set()
    late_count = 0
    future_event_count = 0

    for (lower, upper), quota in zip(months, month_counts, strict=True):
        partition_dir = output_dir / f"event_month={lower:%Y-%m}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        path = partition_dir / "events.jsonl.gz"
        # Only one month of timestamps is buffered; generated event records are not accumulated globally.
        candidate_days = [lower + timedelta(days=offset) for offset in range((upper - lower).days + 1)]
        day_weights = [1.18 if candidate.weekday() >= 5 else 1.0 for candidate in candidate_days]
        timestamps = sorted(_sample_event_time(rng, candidate_days, day_weights, as_of) for _ in range(quota))
        type_counts: Counter[str] = Counter()
        month_late = 0
        with gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6) as stream:
            for event_time in timestamps:
                # Events are time-sorted; expired stories can be evicted from the head of the active list.
                while active_stories and active_stories[0]["expires_at"] <= event_time:
                    active_stories.pop(0)
                event_id += 1
                future_event_count += int(event_time > as_of)
                event_type = rng.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]
                actor = _actor_id(rng, profile_count, hot_profiles)
                target_profile = rng.randint(1, profile_count)
                if target_profile == actor:
                    target_profile = (target_profile % profile_count) + 1
                chosen_post = _pick_post(rng, post_pool)
                if (
                    event_type
                    in {
                        "post_viewed",
                        "like_created",
                        "comment_created",
                        "share_created",
                        "report_created",
                        "media_processed",
                    }
                    and chosen_post is None
                ):
                    event_type = "post_created"
                object_type: str | None = None
                object_id: str | int | None = None
                visibility: str | None = None
                if event_type == "post_created":
                    object_type = "status"
                    object_id = next_post_id
                    visibility = rng.choices(VISIBILITIES, weights=VISIBILITY_WEIGHTS, k=1)[0]
                    post_pool.append(
                        {"id": next_post_id, "author": actor, "created_at": event_time, "visibility": visibility}
                    )
                    next_post_id += 1
                elif event_type in {
                    "post_viewed",
                    "like_created",
                    "comment_created",
                    "share_created",
                    "report_created",
                    "media_processed",
                }:
                    object_type = "status"
                    object_id = chosen_post["id"] if chosen_post else None
                    visibility = chosen_post["visibility"] if chosen_post else None
                elif event_type == "story_created":
                    object_type, object_id = "story", next_story_id
                    active_stories.append(
                        {
                            "id": next_story_id,
                            "created_at": event_time,
                            "expires_at": event_time + timedelta(hours=24),
                        }
                    )
                    next_story_id += 1
                elif event_type == "story_viewed":
                    eligible_stories = active_stories
                    if not eligible_stories:
                        event_type = "story_created"
                        object_type, object_id = "story", next_story_id
                        active_stories.append(
                            {
                                "id": next_story_id,
                                "created_at": event_time,
                                "expires_at": event_time + timedelta(hours=24),
                            }
                        )
                        next_story_id += 1
                    else:
                        object_type = "story"
                        object_id = rng.choice(eligible_stories)["id"]
                elif event_type == "follow_created":
                    object_type, object_id = "profile", target_profile
                elif event_type == "search_performed":
                    object_type, object_id = (
                        "hashtag",
                        rng.choice(
                            [
                                "photography",
                                "streetphotography",
                                "nature",
                                "fediverse",
                                "art",
                                "travel",
                                "opensource",
                                "architecture",
                                "food",
                                "community",
                            ]
                        ),
                    )
                latency = 0 if rng.random() < 0.965 else rng.randint(15 * 60, 72 * 3600)
                ingested = min(as_of, event_time + timedelta(seconds=latency))
                is_late = latency >= 15 * 60 and ingested > event_time
                late_count += int(is_late)
                month_late += int(is_late)
                row = {
                    "run_id": run_id,
                    "event_id": f"pf_evt_{run_id}_{event_id:012d}",
                    "event_timestamp": event_time.isoformat() + "Z",
                    "event_date": event_time.date().isoformat(),
                    "event_hour": event_time.hour,
                    "event_type": event_type,
                    "actor_profile_id": actor,
                    "target_profile_id": target_profile if event_type in {"follow_created", "report_created"} else None,
                    "object_type": object_type,
                    "object_id": object_id,
                    "visibility": visibility,
                    "source_app": rng.choices(SOURCE_APPS, weights=SOURCE_WEIGHTS, k=1)[0],
                    "is_federated": rng.random() < 0.18,
                    "session_id": "ses_" + hashlib.sha1(f"{seed}:{actor}:{event_id // 20}".encode()).hexdigest()[:16],
                    "request_id": hashlib.sha1(f"{seed}:request:{event_id}".encode()).hexdigest()[:24],
                    "ingested_at": ingested.isoformat() + "Z",
                    "is_late_arrival": is_late,
                    "schema_version": 1,
                    "properties": _properties(rng, event_type),
                }
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                all_types[event_type] += 1
                type_counts[event_type] += 1
                distinct_actors.add(actor)
        partition_metadata.append(
            {
                "partition": f"event_month={lower:%Y-%m}",
                "file": f"event_month={lower:%Y-%m}/events.jsonl.gz",
                "rows": quota,
                "late_arrival_rows": month_late,
                "event_type_counts": dict(sorted(type_counts.items())),
                "compressed_bytes": path.stat().st_size,
            }
        )

    total_written = sum(p["rows"] for p in partition_metadata)
    quality = {
        "passed": total_written == event_count and future_event_count == 0,
        "requested_events": event_count,
        "written_events": total_written,
        "unique_event_ids": event_id == event_count,
        "no_future_event_timestamps": future_event_count == 0,
        "month_partitioned": True,
        "streaming_memory_behavior": "Buffers one month's timestamps and event state, not the complete event dataset.",
        "errors": []
        if total_written == event_count and future_event_count == 0
        else [
            *([] if total_written == event_count else [f"Expected {event_count} rows but wrote {total_written}"]),
            *([] if future_event_count == 0 else [f"{future_event_count} event timestamps are after --as-of"]),
        ],
    }
    manifest = {
        "dataset": "PixelFed synthetic activity event stream",
        "classification": "synthetic_only",
        "run_id": run_id,
        "seed": seed,
        "event_count": total_written,
        "profile_population": profile_count,
        "start_timestamp_utc": start_at.isoformat() + "Z",
        "as_of_timestamp_utc": as_of.isoformat() + "Z",
        "partition_column": "event_month derived from event_timestamp",
        "format": "gzip-compressed JSON Lines (one event per line)",
        "event_type_counts": dict(sorted(all_types.items())),
        "distinct_actor_profile_ids": len(distinct_actors),
        "late_arrival_rows": late_count,
        "late_arrival_rate": round(late_count / total_written, 5) if total_written else 0,
        "partitions": partition_metadata,
        "quality_report": quality,
        "business_grains": {
            "event": "one row per activity event",
            "post": "post_created event with stable object_id",
            "engagement": "one row per view, like, comment, share, or report action",
            "follow": "one row per follow_created event",
        },
        "privacy_note": "No real user data, production credentials, private messages, or live API calls are used.",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output_dir / "quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    if not quality["passed"]:
        raise RuntimeError("Activity stream quality checks failed: " + "; ".join(quality["errors"]))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Stream a partitioned synthetic PixelFed activity workload.")
    parser.add_argument("--events", type=int, default=1_000_000, help="Total event rows; streamed one month at a time.")
    parser.add_argument("--profiles", type=int, default=50_000, help="Synthetic actor population size.")
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2024, 1, 1))
    parser.add_argument("--as-of", default="2026-10-26T12:00:00Z")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "activity_stream")
    args = parser.parse_args()
    manifest = generate_stream(
        args.events, args.profiles, args.start_date, _parse_as_of(args.as_of), args.seed, args.output_dir
    )
    print(f"Generated {manifest['event_count']:,} events across {len(manifest['partitions'])} monthly partitions.")
    print(f"Late-arrival rate: {manifest['late_arrival_rate']:.2%}")
    print(f"Manifest: {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
