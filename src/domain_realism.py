"""PixelFed-aware synthetic domain realism and semantic quality checks.

All records are fictional. This module adds plausible relationships and distributions
on top of the schema-exact source replica; it never connects to a live PixelFed service.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

HASHTAGS = [
    "photography",
    "streetphotography",
    "portrait",
    "landscape",
    "nature",
    "wildlife",
    "architecture",
    "travel",
    "food",
    "coffee",
    "art",
    "illustration",
    "filmphotography",
    "opensource",
    "fediverse",
    "pixelfed",
    "community",
    "design",
    "music",
    "books",
    "gardening",
    "sustainability",
    "climate",
    "history",
    "urbanism",
    "cats",
    "dogs",
    "birds",
    "nightphotography",
    "macro",
    "blackandwhite",
    "minimalism",
    "fashion",
    "handmade",
    "craft",
    "cycling",
    "hiking",
    "running",
    "wellbeing",
    "learning",
    "technology",
    "programming",
    "datascience",
    "opensourceart",
    "museum",
    "museumday",
    "weekend",
    "sunset",
    "sunrise",
    "architecturelovers",
    "citylife",
    "ocean",
    "mountains",
    "desert",
    "plants",
    "flowers",
    "concert",
    "streetart",
    "documentary",
    "communitycare",
    "digitalrights",
    "privacy",
    "accessibility",
    "publicspace",
    "localhistory",
    "smallbusiness",
    "makers",
    "printmaking",
    "ceramics",
    "watercolor",
    "sketchbook",
    "film",
    "visualstorytelling",
    "slowtravel",
    "publictransport",
    "foodphotography",
    "homemade",
    "workspace",
    "creativecoding",
    "openweb",
]

POST_TEMPLATES = [
    "A quiet morning walk through {place}; the light changed everything.",
    "Found a small detail in {place} that I had passed a hundred times before.",
    "A little colour study from today's photo walk. What do you notice first?",
    "Weekend notes: good coffee, a long walk, and a camera in my bag.",
    "Trying a different composition and keeping the edit intentionally simple.",
    "A reminder to document the ordinary moments, not only the big ones.",
    "Behind the scenes from a community art session this afternoon.",
    "Experimenting with natural light and a slower shutter speed.",
    "A small collection of textures, shadows, and everyday patterns.",
    "Sharing this for the people who appreciate the quieter corners of the city.",
    "A work in progress from the sketchbook. Feedback is welcome.",
    "Today’s view, captured on the way home. No heavy edits, just the moment.",
]

COMMENT_TEMPLATES = [
    "The light in this is lovely.",
    "I like the detail in the background.",
    "This reminds me of a place I visited last year.",
    "Beautiful colour and composition.",
    "Thanks for sharing the story behind this.",
    "The second detail is my favourite.",
    "Would love to see more from this walk.",
    "Such a calm frame.",
    "This is a great example of keeping the edit simple.",
    "Adding this place to my list.",
]

CITIES = [
    ("Cairo", "Egypt", 30.0444, 31.2357),
    ("Alexandria", "Egypt", 31.2001, 29.9187),
    ("Amman", "Jordan", 31.9539, 35.9106),
    ("Berlin", "Germany", 52.5200, 13.4050),
    ("London", "United Kingdom", 51.5072, -0.1276),
    ("Sao Paulo", "Brazil", -23.5505, -46.6333),
    ("Nairobi", "Kenya", -1.2921, 36.8219),
    ("Tokyo", "Japan", 35.6762, 139.6503),
    ("Toronto", "Canada", 43.6532, -79.3832),
    ("New York", "United States", 40.7128, -74.0060),
    ("Lisbon", "Portugal", 38.7223, -9.1393),
    ("Melbourne", "Australia", -37.8136, 144.9631),
]
LANGUAGES = ["en", "en", "en", "ar", "ar", "de", "fr", "es", "pt", "ja"]
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


def _dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _fmt(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat(sep=" ")


def _sample_time(rng: random.Random, start: datetime, end: datetime, recent: bool = True) -> datetime:
    """Sample activity with a configurable age bias and realistic active-hour clustering."""
    if end <= start:
        return end
    span = max(1, int((end - start).total_seconds()))
    fraction = rng.betavariate(1.35, 1.0) if recent else rng.betavariate(0.9, 1.8)
    candidate = start + timedelta(seconds=min(span, int(span * fraction)))
    hour = rng.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
    candidate = candidate.replace(hour=hour, minute=rng.randrange(60), second=rng.randrange(60), microsecond=0)
    return min(end, max(start, candidate))


def _after(rng: random.Random, created: Any, as_of: datetime, mean_hours: float = 30, max_days: int = 30) -> datetime:
    start = _dt(created) or as_of
    if start >= as_of:
        return as_of
    cap = min((as_of - start).total_seconds(), max_days * 86400)
    seconds = min(cap, max(0, rng.expovariate(1 / max(1, mean_hours * 3600))))
    return min(as_of, start + timedelta(seconds=seconds))


def _put(row: dict[str, Any], key: str, value: Any) -> None:
    if key in row:
        row[key] = value


def apply_domain_realism(generator: Any) -> dict[str, Any]:
    """Replace generic filler in high-value entities/facts with coherent synthetic behavior."""
    rng = random.Random(generator.seed + 91_027)
    data = generator.datasets
    as_of = generator.run_at
    start = generator.start_at
    users = data.get("users", [])
    profiles = data.get("profiles", [])
    local_count = min(len(users), len(profiles))
    profile_by_id = {row["id"]: row for row in profiles}
    profile_ids = list(profile_by_id)
    if not profile_ids:
        return {"applied": True, "reason": "No profiles were generated."}

    hot_count = max(1, int(len(profile_ids) * 0.04))
    hot_profiles = set(rng.sample(profile_ids, min(hot_count, len(profile_ids))))
    profile_weights = [12.0 if pid in hot_profiles else 1.0 for pid in profile_ids]

    profile_created: dict[Any, datetime] = {}
    language_by_profile: dict[Any, str] = {}
    for idx, profile in enumerate(profiles):
        local = idx < local_count
        city = CITIES[rng.randrange(len(CITIES))]
        created = _sample_time(rng, start, as_of, recent=False)
        profile_created[profile["id"]] = created
        language = rng.choices(LANGUAGES, weights=[3, 3, 2, 2, 2, 1, 1, 1, 1, 1], k=1)[0]
        language_by_profile[profile["id"]] = language
        _put(profile, "created_at", _fmt(created))
        _put(profile, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=24, max_days=90)))
        _put(profile, "location", f"{city[0]}, {city[1]}" if rng.random() < 0.68 else None)
        _put(profile, "status", rng.choices(["active", "suspended", "deleted"], [0.955, 0.035, 0.01], k=1)[0])
        _put(profile, "is_private", int(rng.random() < 0.12))
        _put(profile, "unlisted", int(rng.random() < 0.08))
        _put(profile, "is_suggestable", int(rng.random() < 0.72))
        if local:
            user = users[idx]
            _put(user, "created_at", _fmt(created))
            _put(user, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=24, max_days=90)))
            _put(user, "status", rng.choices(["active", "pending", "suspended"], [0.94, 0.035, 0.025], k=1)[0])
            _put(user, "language", language)
            _put(
                user,
                "email_verified_at",
                _fmt(_after(rng, _fmt(created), as_of, mean_hours=12)) if rng.random() < 0.82 else None,
            )
            _put(
                user,
                "deleted_at",
                _fmt(_after(rng, _fmt(created), as_of, mean_hours=1, max_days=365)) if rng.random() < 0.012 else None,
            )
        else:
            _put(profile, "domain", f"node-{(idx - local_count) % 120 + 1:03d}.example.test")

    hashtag_rows = data.get("hashtags", [])
    hashtag_names: list[str] = []
    for idx, row in enumerate(hashtag_rows):
        base = HASHTAGS[idx] if idx < len(HASHTAGS) else f"{HASHTAGS[idx % len(HASHTAGS)]}_{idx + 1}"
        hashtag_names.append(base)
        _put(row, "name", base)
        _put(row, "slug", base.replace("_", "-").lower())
        _put(row, "is_nsfw", int(base in {"fashion", "nightphotography"} and rng.random() < 0.02))
        _put(row, "is_banned", int(rng.random() < 0.002))
        _put(row, "created_at", _fmt(_sample_time(rng, start, as_of, recent=False)))

    place_rows = data.get("places", [])
    for idx, row in enumerate(place_rows):
        city = CITIES[idx % len(CITIES)]
        _put(row, "name", city[0])
        _put(row, "country", city[1])
        _put(row, "slug", f"{city[0].lower().replace(' ', '-')}-{idx + 1:03d}")
        _put(row, "lat", city[2] + rng.uniform(-0.03, 0.03))
        _put(row, "long", city[3] + rng.uniform(-0.03, 0.03))
        _put(row, "created_at", _fmt(_sample_time(rng, start, as_of, recent=False)))

    instances = data.get("instances", [])
    known_hosts = [
        "pixelfed.example.test",
        "social.example.test",
        "photos.example.test",
        "community.example.test",
        "fedi.example.test",
        "open-social.example.test",
        "art.example.test",
        "friends.example.test",
        "media.example.test",
        "local.example.test",
    ]
    for idx, row in enumerate(instances):
        host = known_hosts[idx % len(known_hosts)] if idx < len(known_hosts) else f"node-{idx + 1:03d}.example.test"
        _put(row, "domain", host)
        _put(row, "url", f"https://{host}")
        _put(row, "name", host.split(".")[0].replace("-", " ").title())
        _put(row, "banned", int(rng.random() < 0.04))
        _put(row, "created_at", _fmt(_sample_time(rng, start, as_of, recent=False)))

    statuses = data.get("statuses", [])
    status_by_id: dict[Any, dict[str, Any]] = {}
    topic_by_status: dict[Any, str] = {}
    author_weights = [12.0 if pid in hot_profiles else 1.0 for pid in profile_ids]
    place_ids = [r["id"] for r in place_rows] or [None]
    for idx, row in enumerate(statuses):
        author = rng.choices(profiles, weights=author_weights, k=1)[0]
        pid = author["id"]
        created = _sample_time(rng, profile_created.get(pid, start), as_of, recent=True)
        topic = HASHTAGS[rng.randrange(len(HASHTAGS))]
        city_label = author.get("location") or CITIES[rng.randrange(len(CITIES))][0]
        caption = POST_TEMPLATES[idx % len(POST_TEMPLATES)].format(place=city_label)
        visibility = rng.choices(["public", "unlisted", "followers", "private"], [0.82, 0.08, 0.07, 0.03], k=1)[0]
        post_type = rng.choices(["photo", "video", "text"], [0.69, 0.20, 0.11], k=1)[0]
        _put(row, "profile_id", pid)
        _put(row, "created_at", _fmt(created))
        _put(row, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=24, max_days=45)))
        _put(row, "caption", caption)
        _put(row, "rendered", caption)
        _put(row, "type", post_type)
        _put(row, "visibility", visibility)
        _put(row, "scope", visibility if visibility in {"public", "private", "followers"} else "public")
        _put(row, "language", language_by_profile.get(pid, "en"))
        _put(row, "is_nsfw", int(rng.random() < 0.035))
        _put(row, "local", int(author.get("domain") is None))
        _put(row, "place_id", rng.choice(place_ids) if rng.random() < 0.38 else None)
        _put(row, "in_reply_to_id", None)
        _put(row, "reblog_of_id", None)
        _put(row, "conversation_id", row["id"])
        _put(
            row,
            "deleted_at",
            _fmt(_after(rng, _fmt(created), as_of, mean_hours=12, max_days=180)) if rng.random() < 0.012 else None,
        )
        _put(row, "entities", json.dumps({"hashtags": [topic], "mentions": []}, separators=(",", ":")))
        status_by_id[row["id"]] = row
        topic_by_status[row["id"]] = topic

    # Reply and reblog references always point to an older post in event time.
    chronological_statuses = sorted(statuses, key=lambda r: _dt(r.get("created_at")) or start)
    earlier: list[dict[str, Any]] = []
    for row in chronological_statuses:
        if earlier and rng.random() < 0.16:
            parent = rng.choice(earlier)
            _put(row, "in_reply_to_id", parent["id"])
            _put(row, "conversation_id", parent.get("conversation_id") or parent["id"])
        elif earlier and rng.random() < 0.045:
            _put(row, "reblog_of_id", rng.choice(earlier)["id"])
        earlier.append(row)

    # Engagement follows the post timeline and a heavy-tailed popularity curve.
    popularity = {row["id"]: max(0.2, rng.paretovariate(1.55)) for row in statuses}
    status_choices = statuses or []
    status_weights = [popularity[row["id"]] for row in status_choices]
    used_like_pairs: set[tuple[Any, Any]] = set()
    for row in data.get("likes", []):
        for _ in range(80):
            post = rng.choices(status_choices, weights=status_weights, k=1)[0] if status_choices else None
            actor_id = rng.choices(profile_ids, weights=profile_weights, k=1)[0]
            if (
                post is not None
                and actor_id != post.get("profile_id")
                and (actor_id, post["id"]) not in used_like_pairs
            ):
                break
        if post is not None:
            row["status_id"] = post["id"]
            row["profile_id"] = actor_id
            used_like_pairs.add((actor_id, post["id"]))
            created = _after(rng, post.get("created_at"), as_of, mean_hours=18, max_days=30)
            _put(row, "created_at", _fmt(created))
            _put(row, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=3, max_days=7)))
            _put(
                row,
                "deleted_at",
                _fmt(_after(rng, _fmt(created), as_of, mean_hours=12, max_days=180)) if rng.random() < 0.025 else None,
            )
            _put(row, "flagged", int(rng.random() < 0.002))

    for row in data.get("comments", []):
        post = rng.choices(status_choices, weights=status_weights, k=1)[0] if status_choices else None
        actor_id = rng.choices(profile_ids, weights=profile_weights, k=1)[0]
        if post is not None:
            row["status_id"] = post["id"]
            row["profile_id"] = actor_id
            created = _after(rng, post.get("created_at"), as_of, mean_hours=52, max_days=45)
            _put(row, "created_at", _fmt(created))
            _put(row, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=8, max_days=14)))
            _put(row, "comment", COMMENT_TEMPLATES[rng.randrange(len(COMMENT_TEMPLATES))])
            _put(
                row,
                "deleted_at",
                _fmt(_after(rng, _fmt(created), as_of, mean_hours=12, max_days=180)) if rng.random() < 0.01 else None,
            )

    follow_pairs: set[tuple[Any, Any]] = set()
    for row in data.get("followers", []):
        if len(profile_ids) < 2:
            break
        for _ in range(80):
            actor, target = rng.sample(profile_ids, 2)
            if (actor, target) not in follow_pairs:
                follow_pairs.add((actor, target))
                break
        row["profile_id"], row["following_id"] = actor, target
        created = _sample_time(rng, max(profile_created[actor], profile_created[target]), as_of, recent=True)
        _put(row, "created_at", _fmt(created))
        _put(row, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=24, max_days=90)))
        _put(row, "local_profile", int(profile_by_id[actor].get("domain") is None))
        _put(row, "local_following", int(profile_by_id[target].get("domain") is None))

    for row in data.get("stories", []):
        pid = rng.choices(profile_ids, weights=profile_weights, k=1)[0]
        created = _sample_time(rng, profile_created[pid], as_of, recent=True)
        _put(row, "profile_id", pid)
        _put(row, "created_at", _fmt(created))
        _put(row, "updated_at", _fmt(_after(rng, _fmt(created), as_of, mean_hours=2, max_days=1)))
        _put(row, "expires_at", _fmt(created + timedelta(hours=24)))
        _put(row, "type", rng.choices(["photo", "video"], [0.82, 0.18], k=1)[0])
        _put(row, "mime", "video/mp4" if row.get("type") == "video" else "image/jpeg")
        _put(row, "size", int(rng.lognormvariate(13.0, 1.0)))
        _put(row, "view_count", 0)
        _put(row, "comment_count", 0)

    stories = data.get("stories", [])
    for row in data.get("story_views", []):
        story = rng.choice(stories) if stories else None
        if story is None:
            continue
        row["story_id"] = story["id"]
        row["profile_id"] = rng.choices(profile_ids, weights=profile_weights, k=1)[0]
        created = _dt(story.get("created_at")) or start
        expiry = _dt(story.get("expires_at")) or min(as_of, created + timedelta(hours=24))
        upper = min(as_of, expiry)
        if upper < created:
            upper = created
        seconds = max(0, int((upper - created).total_seconds()))
        viewed = created + timedelta(seconds=rng.randint(0, seconds)) if seconds else created
        _put(row, "created_at", _fmt(viewed))
        _put(row, "updated_at", _fmt(viewed))
    view_counts = Counter(r["story_id"] for r in data.get("story_views", []))
    for story in stories:
        _put(story, "view_count", view_counts.get(story["id"], 0))

    used_tag_pairs: set[tuple[Any, Any]] = set()
    hashtag_ids = [r["id"] for r in hashtag_rows] or [None]
    hashtag_id_by_name = {r.get("name"): r["id"] for r in hashtag_rows}
    for row in data.get("status_hashtags", []):
        if not statuses or not hashtag_rows:
            continue
        post = rng.choices(statuses, weights=status_weights, k=1)[0]
        tag_id = hashtag_id_by_name.get(topic_by_status.get(post["id"]))
        if tag_id is None or rng.random() >= 0.70:
            tag_id = rng.choice(hashtag_ids)
        for _ in range(40):
            if (post["id"], tag_id) not in used_tag_pairs:
                used_tag_pairs.add((post["id"], tag_id))
                break
            post = rng.choice(statuses)
            tag_id = hashtag_id_by_name.get(topic_by_status.get(post["id"]))
            if tag_id is None or rng.random() >= 0.70:
                tag_id = rng.choice(hashtag_ids)
        row["status_id"] = post["id"]
        row["hashtag_id"] = tag_id
        row["profile_id"] = post.get("profile_id")
        _put(row, "status_visibility", post.get("visibility"))
        _put(row, "created_at", post.get("created_at"))
        _put(row, "updated_at", post.get("created_at"))

    hashtag_name_by_id = {row["id"]: row.get("name") for row in hashtag_rows}
    tags_by_status: dict[Any, list[str]] = {}
    for link in data.get("status_hashtags", []):
        tag_name = hashtag_name_by_id.get(link.get("hashtag_id"))
        if tag_name:
            tag_list = tags_by_status.setdefault(link["status_id"], [])
            if tag_name not in tag_list:
                tag_list.append(tag_name)
    for post in statuses:
        raw_entities = post.get("entities")
        try:
            entities = json.loads(raw_entities) if isinstance(raw_entities, str) else raw_entities
        except json.JSONDecodeError:
            entities = {}
        if not isinstance(entities, dict):
            entities = {}
        entities["hashtags"] = tags_by_status.get(post["id"], [])
        entities.setdefault("mentions", [])
        _put(post, "entities", json.dumps(entities, separators=(",", ":"), ensure_ascii=False))

    media_posts = [row for row in statuses if row.get("type") in {"photo", "video"}]
    for row in data.get("media", []):
        post = status_by_id.get(row.get("status_id"))
        if post is None or post.get("type") == "text":
            if media_posts:
                post = rng.choice(media_posts)
                row["status_id"] = post["id"]
            else:
                post = None
        if post is not None:
            _put(row, "created_at", post.get("created_at"))
            _put(row, "caption", post.get("caption"))
        _put(
            row,
            "mime",
            rng.choices(["image/jpeg", "image/webp", "image/png", "video/mp4"], [0.62, 0.16, 0.12, 0.10], k=1)[0],
        )
        _put(row, "size", int(rng.lognormvariate(13.4, 1.15)))
        _put(row, "orientation", rng.choices(["portrait", "landscape", "square"], [0.46, 0.37, 0.17], k=1)[0])
        _put(row, "filter_name", rng.choice(["normal", "clarendon", "lark", "juno", "valencia", "none"]))
        _put(row, "remote_media", int(rng.random() < 0.22))

    # Notifications and ActivityPub-like events reference plausible object types and actions.
    for row in data.get("notifications", []):
        _put(
            row,
            "action",
            rng.choices(["like", "comment", "follow", "mention", "share"], [0.38, 0.28, 0.20, 0.09, 0.05], k=1)[0],
        )
        _put(row, "created_at", _fmt(_sample_time(rng, start, as_of, recent=True)))
        _put(
            row,
            "read_at",
            _fmt(_after(rng, row.get("created_at"), as_of, mean_hours=12)) if rng.random() < 0.58 else None,
        )
    for row in data.get("reports", []):
        if statuses:
            target = rng.choice(statuses)
            _put(row, "object_id", target["id"])
            _put(row, "object_type", "App\\Status")
        _put(
            row,
            "type",
            rng.choices(
                ["spam", "abusive", "copyright", "impersonation", "other"], [0.48, 0.20, 0.10, 0.08, 0.14], k=1
            )[0],
        )
        _put(row, "created_at", _fmt(_sample_time(rng, start, as_of, recent=True)))
        _put(
            row,
            "admin_seen",
            _fmt(_after(rng, row.get("created_at"), as_of, mean_hours=36)) if rng.random() < 0.64 else None,
        )

    metrics = {
        "applied": True,
        "synthetic_only": True,
        "local_profiles": local_count,
        "federated_profiles": max(0, len(profiles) - local_count),
        "hot_profiles": len(hot_profiles),
        "post_rows": len(statuses),
        "like_rows": len(data.get("likes", [])),
        "comment_rows": len(data.get("comments", [])),
        "follow_edges": len(data.get("followers", [])),
        "story_view_rows": len(data.get("story_views", [])),
        "business_semantics": [
            "long-tail creator activity",
            "coherent post-to-engagement chronology",
            "correlated account/profile identities",
            "weighted visibility and content types",
            "meaningful topical tags",
            "story expiry/view chronology",
            "derived engagement counters",
        ],
    }
    return metrics


def validate_domain_quality(generator: Any) -> dict[str, Any]:
    """Assert useful product invariants that a schema-only test cannot catch."""
    data = generator.datasets
    errors: list[str] = []
    posts = {r["id"]: r for r in data.get("statuses", [])}
    profiles = {r["id"]: r for r in data.get("profiles", [])}
    as_of = generator.run_at
    likes_by_post: Counter[Any] = Counter()
    replies_by_post: Counter[Any] = Counter()
    reblogs_by_post: Counter[Any] = Counter()

    for row in data.get("likes", []):
        post = posts.get(row.get("status_id"))
        if post is None:
            errors.append(f"Like {row.get('id')} references a missing post")
            continue
        event_time, post_time = _dt(row.get("created_at")), _dt(post.get("created_at"))
        if event_time and post_time and event_time < post_time:
            errors.append(f"Like {row.get('id')} predates its post")
        if row.get("deleted_at") is None:
            likes_by_post[post["id"]] += 1

    for row in data.get("comments", []):
        post = posts.get(row.get("status_id"))
        if post is None:
            errors.append(f"Comment {row.get('id')} references a missing post")
            continue
        event_time, post_time = _dt(row.get("created_at")), _dt(post.get("created_at"))
        if event_time and post_time and event_time < post_time:
            errors.append(f"Comment {row.get('id')} predates its post")

    for row in data.get("statuses", []):
        if row.get("in_reply_to_id") is not None:
            parent = posts.get(row["in_reply_to_id"])
            if parent is None:
                errors.append(f"Post {row.get('id')} replies to a missing post")
            else:
                replies_by_post[parent["id"]] += 1
        if row.get("reblog_of_id") is not None:
            if row["reblog_of_id"] not in posts:
                errors.append(f"Post {row.get('id')} boosts a missing post")
            else:
                reblogs_by_post[row["reblog_of_id"]] += 1
        created = _dt(row.get("created_at"))
        if created and created > as_of:
            errors.append(f"Post {row.get('id')} is after the as-of timestamp")
        if not row.get("caption") or row.get("caption", "").startswith("synthetic_"):
            errors.append(f"Post {row.get('id')} has placeholder content")

    for row in data.get("statuses", []):
        pid = row["id"]
        if row.get("likes_count") != likes_by_post[pid]:
            errors.append(f"Post {pid} likes_count does not reconcile to active like events")
        if row.get("reply_count") != replies_by_post[pid]:
            errors.append(f"Post {pid} reply_count does not reconcile to post replies")
        if row.get("reblogs_count") != reblogs_by_post[pid]:
            errors.append(f"Post {pid} reblogs_count does not reconcile to boost events")

    follow_pairs: set[tuple[Any, Any]] = set()
    for row in data.get("followers", []):
        actor, target = row.get("profile_id"), row.get("following_id")
        if actor == target:
            errors.append(f"Follow edge {row.get('id')} is a self-follow")
        if (actor, target) in follow_pairs:
            errors.append(f"Duplicate follow edge {actor} -> {target}")
        follow_pairs.add((actor, target))
        if actor not in profiles or target not in profiles:
            errors.append(f"Follow edge {row.get('id')} references a missing profile")

    story_by_id = {r["id"]: r for r in data.get("stories", [])}
    for row in data.get("story_views", []):
        story = story_by_id.get(row.get("story_id"))
        if story is None:
            errors.append(f"Story view {row.get('id')} references a missing story")
            continue
        view_time, created, expiry = (
            _dt(row.get("created_at")),
            _dt(story.get("created_at")),
            _dt(story.get("expires_at")),
        )
        if view_time and created and view_time < created:
            errors.append(f"Story view {row.get('id')} predates its story")
        if view_time and expiry and view_time > expiry:
            errors.append(f"Story view {row.get('id')} occurs after story expiry")

    instance_domains = {
        row.get("domain") for row in data.get("instances", []) if row.get("domain")
    }
    for profile in data.get("profiles", []):
        domain = profile.get("domain")
        if domain and domain not in instance_domains:
            errors.append(f"Federated profile {profile.get('id')} has no matching synthetic instance domain")

    hashtag_name_by_id = {row["id"]: row.get("name") for row in data.get("hashtags", [])}
    hashtags_by_post: dict[Any, set[str]] = {}
    for link in data.get("status_hashtags", []):
        tag_name = hashtag_name_by_id.get(link.get("hashtag_id"))
        if tag_name:
            hashtags_by_post.setdefault(link["status_id"], set()).add(tag_name)
    for post in data.get("statuses", []):
        raw_entities = post.get("entities")
        try:
            entities = json.loads(raw_entities) if isinstance(raw_entities, str) else raw_entities
        except json.JSONDecodeError:
            entities = {}
        embedded_tags = set(entities.get("hashtags", [])) if isinstance(entities, dict) else set()
        bridge_tags = hashtags_by_post.get(post["id"], set())
        if embedded_tags != bridge_tags:
            errors.append(f"Post {post.get('id')} embedded hashtags do not match status_hashtags bridge rows")

    result = {
        "passed": not errors,
        "errors": errors[:100],
        "checks": {
            "post_count": len(posts),
            "like_events": len(data.get("likes", [])),
            "comment_events": len(data.get("comments", [])),
            "follows": len(data.get("followers", [])),
            "story_views": len(data.get("story_views", [])),
            "posts_with_content": sum(bool(r.get("caption")) for r in data.get("statuses", [])),
        },
    }
    return result
