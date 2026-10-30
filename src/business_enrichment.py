"""Business-oriented enrichment for the synthetic PixelFed source replica.

All records remain fictional and deterministic for a fixed seed. This layer improves
cross-table semantics used in analytics without changing table or row counts.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

PROFILE_BIOS = [
    "Photographs everyday architecture, public spaces, and small city details.",
    "Shares nature walks, plants, birds, and quiet outdoor observations.",
    "Explores portraiture, light, and documentary photography.",
    "Collects food stories, neighbourhood cafés, and weekend market moments.",
    "Makes illustrations, sketches, and experiments in visual storytelling.",
    "Shares open-source projects, creative coding, and the open web.",
    "Documents local history, travel notes, and slower journeys.",
    "Studies film photography, colour, grain, and composition.",
    "Explores accessibility, community care, and thoughtful design.",
    "Collects books, museum visits, handmade objects, and studio notes.",
]

COMMENTS = [
    "The light and framing work really well together.",
    "I appreciate the detail you captured in the background.",
    "This feels like a place worth exploring slowly.",
    "The colour palette makes this stand out in my feed.",
    "Thanks for sharing the context behind this image.",
    "I would love to see more from this series.",
    "A lovely reminder to notice ordinary moments.",
    "The composition tells a story without needing much text.",
]

COLLECTIONS = [
    ("Photo walks", "A curated set of details from neighbourhood walks."),
    ("Light studies", "Experiments with colour, shadow, and natural light."),
    ("Nature notes", "Small observations from gardens, trails, and coastlines."),
    ("Places and people", "Documentary moments from local communities."),
    ("Studio journal", "Work in progress, sketches, and creative experiments."),
    ("Travel scrapbook", "Memories from slower journeys and unfamiliar streets."),
    ("Everyday food", "Markets, cafés, homemade dishes, and shared tables."),
    ("Open web", "Creative technology, digital rights, and community projects."),
]

DISCOVER_CATEGORIES = [
    ("Photography", "photography", {"photos_only": 1}),
    ("Nature and wildlife", "nature-wildlife", {"photos_only": 1}),
    ("Architecture and places", "architecture-places", {"local_only": 0}),
    ("Art and illustration", "art-illustration", {"photos_only": 0}),
    ("Food and drink", "food-drink", {"photos_only": 1}),
    ("Travel journals", "travel-journals", {"local_only": 0}),
    ("Community", "community", {"public_only": 1}),
    ("Open technology", "open-technology", {"public_only": 1}),
    ("Local discoveries", "local-discoveries", {"local_only": 1}),
]

DEVICE_PROFILES = [
    ("Android phone", "PixelFedDemo/1.0 (Android; synthetic device)"),
    ("iPhone", "PixelFedDemo/1.0 (iOS; synthetic device)"),
    ("Desktop browser", "PixelFedDemo/1.0 (Windows; synthetic browser)"),
    ("Linux laptop", "PixelFedDemo/1.0 (Linux; synthetic browser)"),
    ("Tablet", "PixelFedDemo/1.0 (tablet; synthetic device)"),
]

REPORT_TYPES = ["spam", "abusive", "copyright", "impersonation", "other"]


def _dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _fmt(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat(sep=" ")


def _put(row: dict[str, Any], key: str, value: Any) -> None:
    if key in row:
        row[key] = value


def _later(
    rng: random.Random,
    occurred_at: Any,
    as_of: datetime,
    mean_hours: float = 24.0,
) -> str:
    """Return a delayed timestamp that never exceeds the generator cutoff."""
    start = _dt(occurred_at) or as_of
    start = min(start, as_of)
    available = max(0.0, (as_of - start).total_seconds())
    delay = min(available, rng.expovariate(1.0 / max(0.01, mean_hours * 3600.0)))
    return _fmt(start + timedelta(seconds=delay))


def _between(rng: random.Random, start_value: Any, end: datetime) -> str:
    start = min(_dt(start_value) or end, end)
    seconds = max(0, int((end - start).total_seconds()))
    return _fmt(start + timedelta(seconds=rng.randint(0, seconds)))


def apply_business_enrichment(generator: Any) -> dict[str, Any]:
    """Enrich existing rows with business semantics without changing their grain."""
    rng = random.Random(generator.seed + 220_411)
    data = generator.datasets
    as_of = generator.run_at
    profiles = data.get("profiles", [])
    users = data.get("users", [])
    statuses = data.get("statuses", [])
    hashtags = data.get("hashtags", [])
    profile_by_id = {row["id"]: row for row in profiles}
    user_by_id = {row["id"]: row for row in users}
    status_by_id = {row["id"]: row for row in statuses}
    profile_ids = list(profile_by_id)
    topic_names = [str(row.get("name") or "photography") for row in hashtags] or ["photography"]
    posts_per_profile = Counter(row.get("profile_id") for row in statuses if row.get("profile_id") is not None)
    ranked_creators = sorted(
        profile_ids,
        key=lambda profile_id: (-posts_per_profile[profile_id], str(profile_id)),
    )
    creator_count = max(1, round(len(ranked_creators) * 0.10)) if ranked_creators else 0
    creator_ids = set(ranked_creators[:creator_count])

    # Topic-aware profiles are more meaningful than generic table/column placeholders.
    for index, profile in enumerate(profiles):
        topic = topic_names[index % len(topic_names)].replace("_", " ").replace("-", " ")
        creator = profile.get("id") in creator_ids
        prefix = "Independent visual creator exploring" if creator else "Community member interested in"
        remote_suffix = " and exchanging ideas across the federated web" if profile.get("domain") else ""
        _put(profile, "bio", f"{prefix} {topic}, everyday stories, and thoughtful composition{remote_suffix}.")
        _put(
            profile,
            "website",
            f"https://portfolio-{profile['id']}.example.test" if creator and rng.random() < 0.65 else None,
        )
        _put(profile, "profile_layout", "grid" if rng.random() < 0.72 else "masonry")
        _put(profile, "post_layout", "masonry" if creator else "grid")

    # A named and readable discovery catalog supports category-level reporting.
    used_slugs: set[str] = set()
    for index, category in enumerate(data.get("discover_categories", [])):
        name, base_slug, flags = DISCOVER_CATEGORIES[index % len(DISCOVER_CATEGORIES)]
        suffix = f"-{index + 1}" if index >= len(DISCOVER_CATEGORIES) else ""
        slug = f"{base_slug}{suffix}"
        while slug in used_slugs:
            slug = f"{base_slug}-{index + 1}"
        used_slugs.add(slug)
        _put(category, "name", name if not suffix else f"{name} {index + 1}")
        _put(category, "slug", slug)
        _put(category, "active", int(rng.random() < 0.92))
        _put(category, "order", index + 1)
        _put(category, "no_nsfw", int(rng.random() < 0.78))
        _put(category, "local_only", flags.get("local_only", 0))
        _put(category, "public_only", flags.get("public_only", 1))
        _put(category, "photos_only", flags.get("photos_only", 0))

    # Device records use documentation-only IP ranges and synthetic user-agent strings.
    documentation_prefixes = ("192.0.2.", "198.51.100.", "203.0.113.")
    devices = data.get("user_devices", [])
    for index, device in enumerate(devices):
        device_name, user_agent = DEVICE_PROFILES[index % len(DEVICE_PROFILES)]
        prefix = documentation_prefixes[index % len(documentation_prefixes)]
        address = f"{prefix}{(index % 253) + 1}"
        user = user_by_id.get(device.get("user_id"))
        account_created = user.get("created_at") if user else generator.start_at
        created_at = _between(rng, account_created, as_of)
        _put(device, "ip", address)
        _put(device, "name", device_name)
        _put(device, "user_agent", user_agent)
        _put(device, "trusted", int(rng.random() < 0.78))
        _put(device, "created_at", created_at)
        _put(device, "last_active_at", _later(rng, created_at, as_of, mean_hours=72))
        _put(device, "updated_at", _later(rng, created_at, as_of, mean_hours=48))

    # Preferences reflect the account's privacy and accessibility context.
    for settings in data.get("user_settings", []):
        user = user_by_id.get(settings.get("user_id"), {})
        profile = profile_by_id.get(user.get("profile_id"), {})
        is_public = not bool(profile.get("is_private", 0))
        _put(settings, "role", "admin" if user.get("is_admin") else "member")
        _put(settings, "crawlable", int(is_public and rng.random() < 0.84))
        _put(settings, "show_discover", int(is_public and rng.random() < 0.88))
        _put(settings, "show_guests", int(is_public and rng.random() < 0.75))
        _put(settings, "public_dm", int(rng.random() < 0.09))
        _put(settings, "compose_media_descriptions", int(rng.random() < 0.52))
        _put(settings, "optimize_screen_reader", int(rng.random() < 0.12))
        _put(settings, "high_contrast_mode", int(rng.random() < 0.07))
        _put(settings, "reduce_motion", int(rng.random() < 0.19))
        _put(settings, "video_autoplay", int(rng.random() < 0.34))
        _put(settings, "always_show_cw", int(rng.random() < 0.21))
        _put(settings, "hide_cw_search", int(rng.random() < 0.17))
        _put(settings, "send_email_new_follower", int(rng.random() < 0.42))
        _put(settings, "send_email_new_follower_request", int(rng.random() < 0.38))
        _put(settings, "send_email_on_share", int(rng.random() < 0.24))
        _put(settings, "send_email_on_like", int(rng.random() < 0.21))
        _put(settings, "send_email_on_mention", int(rng.random() < 0.46))
        _put(settings, "show_profile_followers", int(rng.random() < 0.86))
        _put(settings, "show_profile_follower_count", int(rng.random() < 0.79))
        _put(settings, "show_profile_following", int(rng.random() < 0.72))
        _put(settings, "show_profile_following_count", int(rng.random() < 0.68))

    # Comments are causally linked and avoid self-actions when multiple profiles exist.
    for comment in data.get("comments", []):
        post = status_by_id.get(comment.get("status_id"))
        if post is None:
            continue
        author_id = post.get("profile_id")
        alternatives = [profile_id for profile_id in profile_ids if profile_id != author_id]
        actor_id = rng.choice(alternatives) if alternatives else author_id
        actor = profile_by_id.get(actor_id, {})
        created_at = _later(rng, max(_dt(post["created_at"]), _dt(actor["created_at"])), as_of, mean_hours=52)
        comment_text = COMMENTS[rng.randrange(len(COMMENTS))]
        _put(comment, "profile_id", actor_id)
        _put(comment, "created_at", created_at)
        _put(comment, "updated_at", _later(rng, created_at, as_of, mean_hours=8))
        _put(comment, "rendered_at", _later(rng, created_at, as_of, mean_hours=0.2))
        _put(comment, "comment", comment_text)
        _put(comment, "rendered", comment_text)
        _put(comment, "is_remote", int(bool(actor.get("domain"))))
        _put(comment, "entities", json.dumps({"hashtags": [], "mentions": []}, separators=(",", ":")))

    # MIME family and attachment metadata align with each target status type.
    media_posts = [row for row in statuses if row.get("type") in {"photo", "video"}]
    for media in data.get("media", []):
        post = status_by_id.get(media.get("status_id"))
        if post not in media_posts:
            post = rng.choice(media_posts) if media_posts else None
            _put(media, "status_id", post.get("id") if post else None)
        if post is None:
            _put(media, "profile_id", None)
            _put(media, "user_id", None)
            _put(media, "mime", "image/jpeg")
            continue
        author = profile_by_id.get(post.get("profile_id"), {})
        media_type = post.get("type")
        if media_type == "video":
            mime = "video/mp4"
            license_name = "All rights reserved"
        else:
            mime = rng.choices(["image/jpeg", "image/webp", "image/png"], [0.64, 0.22, 0.14], k=1)[0]
            license_name = rng.choice(["CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC 4.0", "All rights reserved"])
        _put(media, "profile_id", post.get("profile_id"))
        _put(media, "user_id", author.get("user_id"))
        _put(media, "mime", mime)
        _put(media, "caption", post.get("caption"))
        _put(media, "is_nsfw", int(bool(post.get("is_nsfw", 0))))
        _put(media, "remote_media", int(bool(author.get("domain"))))
        _put(media, "license", license_name)
        _put(media, "size", max(10_000, int(rng.lognormvariate(13.4, 1.0))))
        _put(media, "orientation", rng.choices(["portrait", "landscape", "square"], [0.46, 0.37, 0.17], k=1)[0])
        _put(
            media,
            "metadata",
            json.dumps(
                {
                    "synthetic": True,
                    "alt_text_present": bool(post.get("caption")),
                    "media_family": "video" if media_type == "video" else "image",
                    "processing_profile": "video-transcode" if media_type == "video" else "image-optimized",
                    "source_status_id": post.get("id"),
                },
                separators=(",", ":"),
            ),
        )
        _put(media, "created_at", post.get("created_at"))
        _put(media, "updated_at", _later(rng, post.get("created_at"), as_of, mean_hours=24))

    # Content collections have clear themes, visibility, and publication behavior.
    for collection in data.get("collections", []):
        owner = profile_by_id.get(collection.get("profile_id"), {})
        theme_name, description = COLLECTIONS[rng.randrange(len(COLLECTIONS))]
        created_at = _between(rng, owner.get("created_at"), as_of)
        visibility = (
            "followers"
            if owner.get("is_private")
            else rng.choices(["public", "unlisted", "followers"], [0.76, 0.14, 0.10], k=1)[0]
        )
        _put(collection, "title", theme_name)
        _put(collection, "description", description)
        _put(collection, "visibility", visibility)
        _put(collection, "is_nsfw", int(rng.random() < 0.035))
        _put(collection, "created_at", created_at)
        _put(collection, "updated_at", _later(rng, created_at, as_of, mean_hours=24))
        _put(
            collection,
            "published_at",
            _later(rng, created_at, as_of, mean_hours=48) if visibility == "public" and rng.random() < 0.82 else None,
        )

    # Bookmarks occur on or after publication of the saved post.
    for bookmark in data.get("bookmarks", []):
        post = status_by_id.get(bookmark.get("status_id"))
        if post is None:
            continue
        created_at = _later(
            rng,
            max(_dt(post["created_at"]), _dt(profile_by_id[bookmark["profile_id"]]["created_at"])),
            as_of,
            mean_hours=96,
        )
        _put(bookmark, "created_at", created_at)
        _put(bookmark, "updated_at", _later(rng, created_at, as_of, mean_hours=24))

    # Notifications inherit their actor, recipient, item ID, and event time from an event.
    event_pool: list[dict[str, Any]] = []
    for like in data.get("likes", []):
        post = status_by_id.get(like.get("status_id"))
        if post and like.get("profile_id") != post.get("profile_id"):
            event_pool.append(
                {
                    "action": "like",
                    "actor": like.get("profile_id"),
                    "recipient": post.get("profile_id"),
                    "item_id": like.get("id"),
                    "item_type": "App\\Like",
                    "occurred_at": like.get("created_at"),
                    "message": "A profile liked one of your posts.",
                }
            )
    for comment in data.get("comments", []):
        post = status_by_id.get(comment.get("status_id"))
        if post and comment.get("profile_id") != post.get("profile_id"):
            event_pool.append(
                {
                    "action": "comment",
                    "actor": comment.get("profile_id"),
                    "recipient": post.get("profile_id"),
                    "item_id": comment.get("id"),
                    "item_type": "App\\Comment",
                    "occurred_at": comment.get("created_at"),
                    "message": "A profile commented on one of your posts.",
                }
            )
    for follow in data.get("followers", []):
        if follow.get("profile_id") != follow.get("following_id"):
            event_pool.append(
                {
                    "action": "follow",
                    "actor": follow.get("profile_id"),
                    "recipient": follow.get("following_id"),
                    "item_id": follow.get("id"),
                    "item_type": "App\\Follow",
                    "occurred_at": follow.get("created_at"),
                    "message": "A profile followed you.",
                }
            )
    valid_events = [
        event
        for event in event_pool
        if event.get("actor") in profile_by_id
        and event.get("recipient") in profile_by_id
        and event.get("actor") != event.get("recipient")
    ]
    for notification in data.get("notifications", []):
        if not valid_events:
            continue
        event = rng.choice(valid_events)
        created_at = _later(rng, event.get("occurred_at"), as_of, mean_hours=0.1)
        _put(notification, "profile_id", event.get("recipient"))
        _put(notification, "actor_id", event.get("actor"))
        _put(notification, "item_id", event.get("item_id"))
        _put(notification, "item_type", event.get("item_type"))
        _put(notification, "action", event.get("action"))
        _put(notification, "message", event.get("message"))
        _put(notification, "rendered", event.get("message"))
        _put(notification, "created_at", created_at)
        _put(notification, "updated_at", _later(rng, created_at, as_of, mean_hours=2))
        _put(
            notification,
            "read_at",
            _later(rng, created_at, as_of, mean_hours=12) if rng.random() < 0.58 else None,
        )

    # Moderation reports identify the author of an existing post and follow publication.
    for report in data.get("reports", []):
        if not statuses or not profile_ids:
            continue
        target = rng.choice(statuses)
        target_author_id = target.get("profile_id")
        candidates = [profile_id for profile_id in profile_ids if profile_id != target_author_id]
        reporter_id = rng.choice(candidates) if candidates else target_author_id
        report_type = rng.choices(REPORT_TYPES, [0.48, 0.20, 0.10, 0.08, 0.14], k=1)[0]
        created_at = _later(
            rng, max(_dt(target["created_at"]), _dt(profile_by_id[reporter_id]["created_at"])), as_of, mean_hours=18
        )
        _put(report, "profile_id", reporter_id)
        _put(report, "reported_profile_id", target_author_id)
        _put(report, "object_id", target.get("id"))
        _put(report, "object_type", "App\\Status")
        _put(report, "type", report_type)
        _put(report, "message", f"Synthetic moderation case: {report_type} review.")
        _put(report, "created_at", created_at)
        _put(report, "updated_at", _later(rng, created_at, as_of, mean_hours=12))
        _put(report, "admin_seen", _later(rng, created_at, as_of, mean_hours=36) if rng.random() < 0.64 else None)
        _put(report, "spam", int(report_type == "spam"))
        _put(report, "abusive", int(report_type == "abusive"))
        _put(
            report,
            "meta",
            json.dumps(
                {"synthetic": True, "review_queue": "standard", "target_status_id": target.get("id")},
                separators=(",", ":"),
            ),
        )

    # Keep a useful nested object for Power Query JSON expansion exercises.
    for story in data.get("stories", []):
        _put(
            story,
            "story",
            json.dumps(
                {
                    "synthetic": True,
                    "caption": "A short visual moment from the day.",
                    "topics": [topic_names[story["id"] % len(topic_names)]],
                    "format": story.get("type"),
                },
                separators=(",", ":"),
            ),
        )

    return {
        "applied": True,
        "synthetic_only": True,
        "profile_bios_enriched": len(profiles),
        "discover_categories_enriched": len(data.get("discover_categories", [])),
        "device_records_enriched": len(devices),
        "collection_records_enriched": len(data.get("collections", [])),
        "notification_records_enriched": len(data.get("notifications", [])),
        "moderation_reports_enriched": len(data.get("reports", [])),
        "media_records_enriched": len(data.get("media", [])),
        "synthetic_ip_policy": "RFC 5737 documentation-only ranges",
        "business_semantics": [
            "topic-oriented profile descriptions",
            "content-type and MIME-family alignment",
            "notification records tied to engagement events",
            "moderation reports tied to an existing post",
            "bookmark and comment chronology",
            "privacy-aware settings and collections",
            "non-identifying synthetic device metadata",
        ],
    }


def validate_business_enrichment(generator: Any) -> dict[str, Any]:
    """Check cross-table business rules introduced by the enrichment pass."""
    data = generator.datasets
    errors: list[str] = []
    posts = {row["id"]: row for row in data.get("statuses", [])}
    profiles = {row["id"]: row for row in data.get("profiles", [])}
    device_prefixes = ("192.0.2.", "198.51.100.", "203.0.113.")
    media_checked = 0
    media_type_mismatches = 0
    comments_before_posts = 0
    self_comment_events = 0
    bookmarks_before_posts = 0
    reports_before_posts = 0
    reports_with_valid_post_target = 0
    devices_in_documentation_ranges = 0

    for media in data.get("media", []):
        post = posts.get(media.get("status_id"))
        if post is None:
            continue
        media_checked += 1
        post_type = post.get("type")
        mime = str(media.get("mime") or "")
        if post_type == "video" and not mime.startswith("video/"):
            media_type_mismatches += 1
        elif post_type == "photo" and not mime.startswith("image/"):
            media_type_mismatches += 1
        elif post_type == "text":
            media_type_mismatches += 1

    for comment in data.get("comments", []):
        post = posts.get(comment.get("status_id"))
        if post is None:
            continue
        comment_time = _dt(comment.get("created_at"))
        post_time = _dt(post.get("created_at"))
        if comment_time and post_time and comment_time < post_time:
            comments_before_posts += 1
        if len(profiles) > 1 and comment.get("profile_id") == post.get("profile_id"):
            self_comment_events += 1

    for bookmark in data.get("bookmarks", []):
        post = posts.get(bookmark.get("status_id"))
        if post is None:
            continue
        bookmark_time = _dt(bookmark.get("created_at"))
        post_time = _dt(post.get("created_at"))
        if bookmark_time and post_time and bookmark_time < post_time:
            bookmarks_before_posts += 1

    for report in data.get("reports", []):
        if report.get("object_type") != "App\\Status":
            continue
        post = posts.get(report.get("object_id"))
        if post is None:
            errors.append(f"Report {report.get('id')} references a missing status")
            continue
        reports_with_valid_post_target += 1
        report_time = _dt(report.get("created_at"))
        post_time = _dt(post.get("created_at"))
        if report_time and post_time and report_time < post_time:
            reports_before_posts += 1
        if report.get("reported_profile_id") != post.get("profile_id"):
            errors.append(f"Report {report.get('id')} target profile does not match its status author")

    for device in data.get("user_devices", []):
        ip = str(device.get("ip") or "")
        if ip.startswith(device_prefixes):
            devices_in_documentation_ranges += 1
        else:
            errors.append(f"Device {device.get('id')} IP is outside the reserved documentation ranges")

    if media_type_mismatches:
        errors.append(f"{media_type_mismatches} media records have a MIME family inconsistent with the post type")
    if comments_before_posts:
        errors.append(f"{comments_before_posts} comments predate their target post")
    if self_comment_events:
        errors.append(f"{self_comment_events} comment events are self-comments despite multiple profiles existing")
    if bookmarks_before_posts:
        errors.append(f"{bookmarks_before_posts} bookmarks predate their target post")
    if reports_before_posts:
        errors.append(f"{reports_before_posts} moderation reports predate their target post")

    profile_bios = sum(
        bool(row.get("bio")) and not str(row.get("bio")).startswith("synthetic_") for row in data.get("profiles", [])
    )
    categories_named = sum(
        bool(row.get("name")) and not str(row.get("name")).startswith("synthetic_")
        for row in data.get("discover_categories", [])
    )
    checks = {
        "profile_bios": profile_bios,
        "categories_named": categories_named,
        "media_records_checked": media_checked,
        "media_type_mismatches": media_type_mismatches,
        "comments_before_posts": comments_before_posts,
        "self_comment_events": self_comment_events,
        "bookmarks_before_posts": bookmarks_before_posts,
        "reports_before_posts": reports_before_posts,
        "reports_with_valid_post_target": reports_with_valid_post_target,
        "device_ips_in_documentation_ranges": devices_in_documentation_ranges,
        "device_ip_count": len(data.get("user_devices", [])),
    }
    return {"passed": not errors, "errors": errors[:100], "checks": checks}
