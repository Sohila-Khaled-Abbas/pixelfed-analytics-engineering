# Power BI Model Guide

## Recommended initial star schema

### Dimensions
- `DimDate`: one row per calendar date; mark it as the date table.
- `DimProfile`: one row per `profiles.id`, with selected public profile and account attributes.
- `DimStatus`: one row per `statuses.id`, with type, visibility, scope, NSFW flag, and content-creation date.
- `DimHashtag`: one row per `hashtags.id`; use the `status_hashtags` bridge when analyzing tags per post.

### Facts and bridge tables
- `FactPostMetrics`: one row per status; stored likes/reblogs/replies counters and post date.
- `FactLikes`: one row per like event, keyed by `likes.id`.
- `FactComments`: one row per comment, keyed by `comments.id`.
- `FactMedia`: one row per media record, keyed by `media.id`.
- `FactFollows`: one row per directed follower relationship.
- `BridgeStatusHashtag`: one row per post/hashtag association.

## Modeling rules

- Confirm key uniqueness before creating 1:* relationships.
- Prefer single-direction filter flow from dimensions to facts.
- Use role-playing profile dimensions when the same fact has follower/followed, sender/recipient, or actor/recipient roles.
- Keep facts at separate grains. A status with 4 likes, 3 comments and 2 media records can create a 24-row joined fan-out if flattened directly.
- Distinguish stored counters on `statuses` from event counts in `likes` and `comments`; synthetic counters may not reconcile exactly.
- Handle soft deletes deliberately (`deleted_at`). Preserve the source value in staging, then document whether each report metric excludes deleted records.
- Exclude passwords, tokens, private keys, reset tokens, secrets, session payloads, and unnecessary PII from report-facing tables.

## Starter DAX measures

```dax
Total Posts = DISTINCTCOUNT(FactPostMetrics[StatusID])

Like Events =
CALCULATE(
    COUNTROWS(FactLikes),
    ISBLANK(FactLikes[deleted_at])
)

Comment Events = COUNTROWS(FactComments)

Media Items = DISTINCTCOUNT(FactMedia[MediaID])

Average Stored Likes per Post =
DIVIDE(
    SUM(FactPostMetrics[likes_count]),
    [Total Posts]
)
```

Align column names in the curated tables with the DAX measures or update the measures to match your model.
