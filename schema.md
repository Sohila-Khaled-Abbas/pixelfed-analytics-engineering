# Schema: Pixelfed - MySQL

Database: mysql
Tables: 54
Columns are NOT NULL unless marked nullable.

## account_logs

id: bigint PK
user_id: bigint FK indexed
item_id: bigint nullable
item_type: varchar nullable
action: varchar nullable
message: varchar nullable
link: varchar nullable
ip_address: varchar nullable
user_agent: varchar nullable
metadata: json nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## activities

id: bigint PK
to_id: bigint nullable
from_id: bigint nullable
object_type: varchar nullable
data: json nullable
processed_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## avatars

id: bigint PK
profile_id: bigint FK unique
media_path: varchar nullable
thumb_path: varchar nullable
remote_url: varchar indexed nullable
change_count: int
last_fetched_at: timestamp nullable
last_processed_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable

## bookmarks

id: int PK
status_id: bigint FK
profile_id: bigint FK
created_at: timestamp nullable
updated_at: timestamp nullable

## circle_profiles

id: bigint PK
owner_id: bigint indexed nullable
circle_id: bigint FK indexed
profile_id: bigint FK indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## circles

id: bigint PK
profile_id: bigint FK indexed
name: varchar nullable
description: text nullable
scope: varchar
bcc: tinyint
active: tinyint indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## collection_items

id: bigint PK
collection_id: bigint FK indexed
order: int nullable
object_type: varchar indexed
object_id: bigint indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## collections

id: bigint PK
profile_id: bigint FK nullable
title: varchar nullable
description: text nullable
is_nsfw: tinyint
visibility: varchar indexed
published_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## comments

id: bigint PK
profile_id: bigint FK
user_id: bigint FK nullable
status_id: bigint FK
comment: text nullable
rendered: text nullable
entities: json nullable
is_remote: tinyint
rendered_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## contacts

id: bigint PK
user_id: bigint FK indexed
response_requested: tinyint
message: text
response: text
read_at: timestamp nullable
responded_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## direct_messages

id: bigint PK
to_id: bigint indexed
from_id: bigint indexed
from_profile_ids: varchar nullable
group_message: tinyint
status_id: bigint FK
read_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## discover_categories

id: bigint PK
name: varchar nullable
slug: varchar unique
active: tinyint indexed
order: tinyint
media_id: bigint FK unique nullable
no_nsfw: tinyint
local_only: tinyint
public_only: tinyint
photos_only: tinyint
active_until: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## discover_category_hashtags

id: bigint PK
discover_category_id: bigint FK indexed
hashtag_id: bigint FK indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## email_verifications

id: bigint PK
user_id: bigint FK
email: varchar nullable
user_token: varchar indexed
random_token: varchar indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## failed_jobs

id: bigint PK
connection: text
queue: text
payload: longtext
exception: longtext
failed_at: timestamp

## follow_requests

id: bigint PK
follower_id: bigint FK indexed
following_id: bigint indexed
is_rejected: tinyint
is_local: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable

## followers

id: int PK
profile_id: bigint FK
following_id: bigint
local_profile: tinyint indexed
local_following: tinyint indexed
created_at: timestamp indexed nullable
updated_at: timestamp nullable

## hashtag_follows

id: bigint PK
user_id: bigint FK indexed
profile_id: bigint FK indexed
hashtag_id: bigint FK indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## hashtags

id: bigint PK
name: varchar unique
slug: varchar unique
is_nsfw: tinyint
is_banned: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable

## import_datas

id: int PK
profile_id: bigint FK
job_id: bigint FK nullable
service: varchar
path: varchar nullable
stage: tinyint
original_name: varchar nullable
import_accepted: tinyint nullable
completed_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## import_jobs

id: int PK
profile_id: bigint FK
service: varchar
uuid: varchar nullable
storage_path: varchar nullable
stage: tinyint
media_json: text nullable
completed_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## instances

id: bigint PK
domain: varchar unique
url: varchar nullable
name: varchar nullable
admin_url: varchar nullable
limit_reason: varchar nullable
unlisted: tinyint
auto_cw: tinyint
banned: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable

## jobs

id: bigint PK
queue: varchar indexed
payload: longtext
attempts: tinyint
reserved_at: int nullable
available_at: int
created_at: int

## likes

id: bigint PK
profile_id: bigint FK
status_id: bigint FK
flagged: tinyint
created_at: timestamp indexed nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable

## media

id: int PK
status_id: bigint FK nullable
profile_id: bigint FK nullable
user_id: bigint FK indexed nullable
is_nsfw: tinyint
remote_media: tinyint
original_sha256: varchar indexed nullable
optimized_sha256: varchar indexed nullable
media_path: varchar
thumbnail_path: varchar nullable
cdn_url: varchar nullable
optimized_url: varchar nullable
thumbnail_url: varchar nullable
remote_url: varchar nullable
caption: varchar nullable
hls_path: varchar nullable
order: tinyint
mime: varchar nullable
size: int nullable
orientation: varchar nullable
filter_name: varchar nullable
filter_class: varchar nullable
license: varchar nullable
processed_at: timestamp nullable
hls_transcoded_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable
key: varchar nullable
metadata: json nullable
version: tinyint

## mentions

id: bigint PK
status_id: bigint FK
profile_id: bigint FK
local: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable

## migrations

id: int PK
migration: varchar
batch: int

## mod_logs

id: bigint PK
user_id: bigint FK indexed
user_username: varchar nullable
object_uid: bigint indexed nullable
object_id: bigint indexed nullable
object_type: varchar indexed nullable
action: varchar nullable
message: text nullable
metadata: json nullable
access_level: varchar nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## newsroom

id: bigint PK
user_id: bigint FK nullable
header_photo_url: varchar nullable
title: varchar nullable
slug: varchar unique nullable
category: varchar
summary: text nullable
body: text nullable
body_rendered: text nullable
link: varchar nullable
force_modal: tinyint
show_timeline: tinyint
show_link: tinyint
auth_only: tinyint
published_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## notifications

id: bigint PK
profile_id: bigint FK indexed
actor_id: bigint indexed nullable
item_id: bigint nullable
item_type: varchar nullable
action: varchar nullable
message: varchar nullable
rendered: varchar nullable
read_at: timestamp nullable
created_at: timestamp indexed nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable

## oauth_access_tokens

id: varchar PK
user_id: bigint FK indexed nullable
client_id: int
name: varchar nullable
scopes: text nullable
revoked: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable
expires_at: datetime nullable

## oauth_auth_codes

id: varchar PK
user_id: bigint FK
client_id: int
scopes: text nullable
revoked: tinyint
expires_at: datetime nullable

## oauth_clients

id: int PK
user_id: bigint FK indexed nullable
name: varchar
secret: varchar
redirect: text
personal_access_client: tinyint
password_client: tinyint
revoked: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable

## oauth_personal_access_clients

id: int PK
client_id: int indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## oauth_refresh_tokens

id: varchar PK
access_token_id: varchar FK indexed
revoked: tinyint
expires_at: datetime nullable

## pages

id: bigint PK
root: varchar indexed nullable
slug: varchar unique nullable
title: varchar nullable
category_id: int indexed nullable
content: longtext nullable
template: varchar indexed
active: tinyint indexed
cached: tinyint indexed
active_until: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## password_resets

email: varchar indexed
token: varchar
created_at: timestamp nullable

## places

id: bigint PK
slug: varchar indexed
name: varchar indexed
country: varchar indexed
aliases: json nullable
lat: decimal nullable
long: decimal nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## profile_sponsors

id: bigint PK
profile_id: bigint FK unique
sponsors: json nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## profiles

id: bigint PK
user_id: int FK nullable
domain: varchar indexed nullable
username: varchar indexed nullable
status: varchar indexed nullable
name: varchar nullable
bio: text nullable
unlisted: tinyint indexed
cw: tinyint indexed
no_autolink: tinyint indexed
location: varchar nullable
website: varchar nullable
profile_layout: varchar nullable
header_bg: varchar nullable
post_layout: varchar nullable
is_private: tinyint
sharedInbox: varchar indexed nullable
inbox_url: varchar nullable
outbox_url: varchar nullable
key_id: varchar unique nullable
follower_url: varchar nullable
following_url: varchar nullable
private_key: text nullable
public_key: text nullable
remote_url: varchar nullable
created_at: timestamp nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable
delete_after: timestamp nullable
is_suggestable: tinyint indexed
last_fetched_at: timestamp nullable
status_count: int nullable
followers_count: int nullable
following_count: int nullable
webfinger: varchar unique nullable
avatar_url: varchar nullable

## report_comments

id: int PK
report_id: bigint FK indexed
profile_id: bigint FK
user_id: bigint FK
comment: text
created_at: timestamp nullable
updated_at: timestamp nullable

## report_logs

id: int PK
profile_id: bigint FK
item_id: bigint nullable
item_type: varchar nullable
action: varchar nullable
system_message: tinyint
metadata: json nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## reports

id: bigint PK
profile_id: bigint FK
user_id: bigint FK nullable
object_id: bigint
object_type: varchar nullable
reported_profile_id: bigint nullable
type: varchar nullable
message: varchar nullable
admin_seen: timestamp nullable
not_interested: tinyint
spam: tinyint
nsfw: tinyint
abusive: tinyint
meta: json nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## sessions

id: varchar unique
user_id: bigint FK nullable
ip_address: varchar nullable
user_agent: text nullable
payload: text
last_activity: int

## status_hashtags

id: bigint PK
status_id: bigint FK indexed
hashtag_id: bigint FK indexed
profile_id: bigint FK indexed nullable
status_visibility: varchar indexed nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## statuses

id: bigint PK
uri: varchar unique indexed nullable
caption: text nullable
rendered: text nullable
profile_id: bigint FK indexed nullable
type: varchar indexed nullable
in_reply_to_id: bigint nullable
reblog_of_id: bigint nullable
url: varchar nullable
is_nsfw: tinyint indexed
scope: varchar indexed
visibility: enum indexed
reply: tinyint
likes_count: bigint
reblogs_count: bigint
language: varchar nullable
conversation_id: bigint nullable
local: tinyint indexed
application_id: bigint nullable
in_reply_to_profile_id: bigint nullable
entities: json nullable
created_at: timestamp indexed nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable
cw_summary: varchar nullable
reply_count: int nullable
comments_disabled: tinyint
place_id: bigint FK indexed nullable
object_url: varchar unique nullable

## stories

id: bigint PK
profile_id: bigint FK indexed
type: varchar nullable
size: int nullable
mime: varchar nullable
duration: smallint
path: varchar nullable
cdn_url: varchar nullable
public: tinyint indexed
local: tinyint indexed
view_count: int nullable
comment_count: int nullable
story: json nullable
expires_at: timestamp indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## story_views

id: bigint PK
story_id: bigint FK indexed
profile_id: bigint FK indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## user_devices

id: bigint PK
user_id: bigint FK indexed
ip: varchar indexed
user_agent: varchar indexed
fingerprint: varchar nullable
name: varchar nullable
trusted: tinyint nullable
last_active_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## user_filters

id: bigint PK
user_id: bigint FK indexed
filterable_id: bigint
filterable_type: varchar
filter_type: varchar indexed
created_at: timestamp nullable
updated_at: timestamp nullable

## user_invites

id: bigint PK
user_id: bigint FK indexed
profile_id: bigint FK indexed
email: varchar unique
message: text nullable
key: varchar
token: varchar
valid_until: timestamp nullable
used_at: timestamp indexed nullable
created_at: timestamp nullable
updated_at: timestamp nullable

## user_settings

id: bigint PK
user_id: bigint FK unique
role: varchar
crawlable: tinyint
show_guests: tinyint
show_discover: tinyint
public_dm: tinyint
hide_cw_search: tinyint
hide_blocked_search: tinyint
always_show_cw: tinyint
compose_media_descriptions: tinyint
reduce_motion: tinyint
optimize_screen_reader: tinyint
high_contrast_mode: tinyint
video_autoplay: tinyint
send_email_new_follower: tinyint
send_email_new_follower_request: tinyint
send_email_on_share: tinyint
send_email_on_like: tinyint
send_email_on_mention: tinyint
created_at: timestamp nullable
updated_at: timestamp nullable
show_profile_followers: tinyint
show_profile_follower_count: tinyint
show_profile_following: tinyint
show_profile_following_count: tinyint

## users

id: bigint PK
profile_id: bigint FK unique nullable
name: varchar nullable
username: varchar unique nullable
email: varchar unique
status: varchar indexed nullable
language: varchar indexed nullable
password: varchar
remember_token: varchar nullable
is_admin: tinyint
email_verified_at: timestamp nullable
created_at: timestamp nullable
updated_at: timestamp nullable
deleted_at: timestamp indexed nullable
2fa_enabled: tinyint
2fa_secret: varchar nullable
2fa_backup_codes: json nullable
2fa_setup_at: timestamp nullable
delete_after: timestamp nullable

## websockets_statistics_entries

id: int PK
app_id: varchar
peak_connection_count: int
websocket_message_count: int
api_message_count: int
created_at: timestamp nullable
updated_at: timestamp nullable

## Relationships

circles.id → circle_profiles.circle_id (one-to-many)
collections.id → collection_items.collection_id (one-to-many)
discover_categories.id → discover_category_hashtags.discover_category_id (one-to-many)
followers.id → follow_requests.follower_id (one-to-many)
hashtags.id → discover_category_hashtags.hashtag_id (one-to-many)
hashtags.id → hashtag_follows.hashtag_id (one-to-many)
hashtags.id → status_hashtags.hashtag_id (one-to-many)
jobs.id → import_datas.job_id (one-to-many)
media.id → discover_categories.media_id (one-to-many)
oauth_refresh_tokens.access_token_id → oauth_access_tokens.id (many-to-one)
places.id → statuses.place_id (one-to-many)
profiles.id → avatars.profile_id (one-to-many)
profiles.id → bookmarks.profile_id (one-to-many)
profiles.id → circle_profiles.profile_id (one-to-many)
profiles.id → circles.profile_id (one-to-many)
profiles.id → collections.profile_id (one-to-many)
profiles.id → comments.profile_id (one-to-many)
profiles.id → followers.profile_id (one-to-many)
profiles.id → hashtag_follows.profile_id (one-to-many)
profiles.id → import_datas.profile_id (one-to-many)
profiles.id → import_jobs.profile_id (one-to-many)
profiles.id → likes.profile_id (one-to-many)
profiles.id → media.profile_id (one-to-many)
profiles.id → mentions.profile_id (one-to-many)
profiles.id → notifications.profile_id (one-to-many)
profiles.id → profile_sponsors.profile_id (one-to-many)
profiles.id → report_comments.profile_id (one-to-many)
profiles.id → report_logs.profile_id (one-to-many)
profiles.id → reports.profile_id (one-to-many)
profiles.id → status_hashtags.profile_id (one-to-many)
profiles.id → statuses.profile_id (one-to-many)
profiles.id → stories.profile_id (one-to-many)
profiles.id → story_views.profile_id (one-to-many)
profiles.id → user_invites.profile_id (one-to-many)
profiles.id → users.profile_id (one-to-many)
reports.id → report_comments.report_id (one-to-many)
statuses.id → bookmarks.status_id (one-to-many)
statuses.id → comments.status_id (one-to-many)
statuses.id → direct_messages.status_id (one-to-many)
statuses.id → likes.status_id (one-to-many)
statuses.id → media.status_id (one-to-many)
statuses.id → mentions.status_id (one-to-many)
statuses.id → status_hashtags.status_id (one-to-many)
stories.id → story_views.story_id (one-to-many)
users.id → account_logs.user_id (one-to-many)
users.id → comments.user_id (one-to-many)
users.id → contacts.user_id (one-to-many)
users.id → email_verifications.user_id (one-to-many)
users.id → hashtag_follows.user_id (one-to-many)
users.id → media.user_id (one-to-many)
users.id → mod_logs.user_id (one-to-many)
users.id → newsroom.user_id (one-to-many)
users.id → oauth_access_tokens.user_id (one-to-many)
users.id → oauth_auth_codes.user_id (one-to-many)
users.id → oauth_clients.user_id (one-to-many)
users.id → profiles.user_id (one-to-many)
users.id → report_comments.user_id (one-to-many)
users.id → reports.user_id (one-to-many)
users.id → sessions.user_id (one-to-many)
users.id → user_devices.user_id (one-to-many)
users.id → user_filters.user_id (one-to-many)
users.id → user_invites.user_id (one-to-many)
users.id → user_settings.user_id (one-to-many)

## Indexes

bookmarks.bookmarks_status_id_profile_id_unique (unique): status_id, profile_id
circle_profiles.circle_profiles_circle_id_profile_id_unique (unique): circle_id, profile_id
direct_messages.direct_messages_to_id_from_id_status_id_unique (unique): to_id, from_id, status_id
discover_category_hashtags.discover_category_hashtags_discover_category_id_hashtag_id_unique (unique): discover_category_id, hashtag_id
followers.followers_profile_id_following_id_unique (unique): profile_id, following_id
hashtag_follows.hashtag_follows_user_id_profile_id_hashtag_id_unique (unique): user_id, profile_id, hashtag_id
import_datas.import_datas_job_id_original_name_unique (unique): job_id, original_name
likes.likes_profile_id_status_id_unique (unique): profile_id, status_id
media.media_status_id_media_path_unique (unique): status_id, media_path
places.places_slug_country_lat_long_unique (unique): slug, country, lat, long
profiles.profiles_domain_username_unique (unique): domain, username
reports.reports_user_id_object_id_object_type_unique (unique): user_id, object_id, object_type
status_hashtags.status_hashtags_status_id_hashtag_id_unique (unique): status_id, hashtag_id
statuses.statuses_in_reply_to_id_reblog_of_id_index (index): in_reply_to_id, reblog_of_id
stories.stories_profile_id_path_unique (unique): profile_id, path
story_views.story_views_story_id_profile_id_unique (unique): story_id, profile_id
user_devices.user_devices_user_id_ip_user_agent_fingerprint_unique (unique): user_id, ip, user_agent, fingerprint
user_filters.user_filters_user_id_filterable_id_filterable_type_filter_type_unique (unique): user_id, filterable_id, filterable_type, filter_type

---
If you suggest changes to this schema, ALSO return them as a DrawSQL patch: one fenced ```json code block, so I can apply them to my diagram. If you are only answering a question, skip the patch.

Patch rules:

- One JSON object with "strategy": "merge"; combine every change into that single patch.
- Reference tables and columns by name. Only include what changes — omit unchanged columns and unused optional fields.
- Column: {"name","type","length","is_primary_key","is_auto_increment","is_nullable","is_unique_key","is_index","is_unsigned","default","enum_values"} — use exact type names for mysql as shown in the schema above.
- Relationship: {"type":"one-to-many","source_table":"users","source_column":"id","target_table":"posts","target_column":"user_id"} — for "one-to-many" the source is the "one" side; for "many-to-one" the source is the "many" (foreign-key) side. Prefer "one-to-many".
- Add "default_type" ("string" | "function" | "number" | "boolean") when a default could be misread — a literal string "CURRENT_TIMESTAMP" or "0" needs "default_type":"string".
- SET columns (MySQL) list their members in "set_values", not "enum_values".
- Index: {"indexes":[{"name":"idx_posts_user_created","type":"index","columns":["user_id","created_at"]}]} on its table — "type" is "index" or "unique"; delete via "deletions".
- Group: {"name":"Billing"}. A group never lists its members — put "parent_name":"Billing" on each table that belongs to it.
- Sticky note: {"sticky_notes":[{"content":"..."}]}.
- Delete via "deletions"; rename via "old_name". Do not include left/top coordinates.

Examples:
Add table: `{"strategy":"merge","tables":[{"name":"posts","comment":"Blog posts","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true},{"name":"user_id","type":"bigint","is_index":true},{"name":"title","type":"varchar","length":255},{"name":"body","type":"text","is_nullable":true},{"name":"created_at","type":"timestamp","is_nullable":true},{"name":"updated_at","type":"timestamp","is_nullable":true}]}]}`
Rename table and column (use old_name only when renaming): `{"strategy":"merge","tables":[{"name":"articles","old_name":"posts","columns":[{"name":"content","old_name":"body"}]}]}`
Delete: `{"strategy":"merge","deletions":{"tables":["tmp"],"columns":[{"table":"users","columns":["legacy"]}],"relationships":[{"source_table":"users","source_column":"id","target_table":"posts","target_column":"user_id"}]}}`
Multiple groups with nested tables (every table sets parent_name): `{"strategy":"merge","groups":[{"name":"Auth"},{"name":"Content"}],"tables":[{"name":"users","parent_name":"Auth","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true}]},{"name":"roles","parent_name":"Auth","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true}]},{"name":"posts","parent_name":"Content","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true}]}]}`
