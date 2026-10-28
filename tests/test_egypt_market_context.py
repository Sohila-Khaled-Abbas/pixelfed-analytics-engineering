"""Reference-catalog tests for the Egypt market context layer."""

from __future__ import annotations

from egypt_market_context import (
    CATEGORIES,
    GOVERNORATES,
    MARKET_PROFILE,
    TOPICS,
    _tag_catalog,
)


def test_egypt_governorate_catalog_has_all_27_unique_entries():
    assert len(GOVERNORATES) == 27
    assert len({row["slug"] for row in GOVERNORATES}) == 27
    assert all(row["population"] > 0 for row in GOVERNORATES)
    assert all(0 <= row["urban_pct"] <= 100 for row in GOVERNORATES)
    assert all(row["population"] == row["urban_population"] + row["rural_population"] for row in GOVERNORATES)
    assert sum(row["population"] for row in GOVERNORATES) == 105_914_499
    assert sum(row["urban_population"] for row in GOVERNORATES) == 45_460_262
    assert sum(row["rural_population"] for row in GOVERNORATES) == 60_454_237
    assert all(row["reference_date"] == "2024-01-01" for row in GOVERNORATES)
    assert all("capmas.gov.eg" in row["population_source_url"] for row in GOVERNORATES)
    assert {row["en"] for row in GOVERNORATES} >= {"Cairo", "Alexandria", "Damietta", "Giza"}


def test_bilingual_topics_and_discovery_categories_are_well_formed():
    assert len(TOPICS) >= 8
    assert all(row["captions_ar"] and row["captions_en"] for row in TOPICS)
    assert all(row["bio_ar"] and row["bio_en"] for row in TOPICS)
    assert len(CATEGORIES) == 9
    assert all(len(row) == 2 for row in CATEGORIES)
    assert len({row[1] for row in CATEGORIES}) == len(CATEGORIES)


def test_generated_hashtag_catalog_has_unique_source_keys():
    tags = _tag_catalog(150)
    assert len(tags) == 150
    assert len({row["name"] for row in tags}) == 150
    assert len({row["slug"] for row in tags}) == 150



def test_market_profile_assumptions_are_configured_and_valid():
    assert MARKET_PROFILE["profile_id"] == "egypt_visual_creator_analytics_v1"

    probability_fields = (
        "population_urban_propensity_factor",
        "creator_cohort_share",
        "local_location_disclosure_rate",
        "federated_location_disclosure_rate",
        "creator_bio_presence_rate",
        "community_bio_presence_rate",
        "creator_website_presence_rate",
        "post_topic_stickiness",
        "caption_followup_rate",
        "comment_followup_rate",
        "post_place_tagging_rate",
        "bio_variant_addition_rate",
        "profile_grid_layout_share",
        "discovery_category_active_rate",
    )
    assert all(0 <= MARKET_PROFILE[field] <= 1 for field in probability_fields)

    for field in ("local_language_mix", "federated_language_mix", "admin_content_language_mix"):
        weights = MARKET_PROFILE[field]
        assert all(weight >= 0 for weight in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 1e-9
