# Egypt Market Context for the Synthetic Dataset

## Intended business scenario

This version is an **Egypt-focused visual-content, creator, and local-business analytics dataset** built on the existing PixelFed-inspired schema. It can support questions about public posts, media formats, likes, comments, engagement lag, content themes, optional profile disclosure, local versus federated users, and the distribution of synthetic activity across Egyptian governorates.

The schema does **not** contain orders, payments, inventory, advertising spend, website sessions, or verified conversions. Do not claim EGP revenue, customer acquisition cost, ROAS, sales, or conversion rates from social events. For an e-commerce portfolio problem, add commerce tables and a real public commerce dataset rather than inventing sales metrics on top of these tables.

## Public reference inputs

| Input | Snapshot | How it is used | What it does not prove |
|---|---|---|---|
| [CAPMAS population estimates by governorate (urban/rural), 1 January 2024](https://www.capmas.gov.eg/Admin/Pages%20Files/20245121324361-%20pop_new.pdf) | Published population totals and urban share for all 27 governorates | Governorate catalogue and a transparent population-proportional geography sampling prior | It is not a measured distribution of social-platform users or creators by governorate |
| [World Bank WDI: individuals using the Internet, Egypt (IT.NET.USER.ZS)](https://data.worldbank.org/indicator/IT.NET.USER.ZS?locations=EG) | 2024 value: 75% of the population; the World Bank page lists ITU as the source | Context for digital access and representativeness limitations | It does not estimate use of this specific platform |
| [DataReportal, Digital 2026: Egypt](https://datareportal.com/reports/digital-2026-egypt) | Most recent figures mostly describe October/end-2025: 98.2 million internet users and 51.6 million social-media user identities reported | Market framing and source-date documentation | Social-media user identities may not be unique people; these are not PixelFed account counts |
| [DrawSQL PixelFed template](https://drawsql.app/templates/pixelfed) and repository schema.md | Operational schema contract | Table, column, and key compatibility | It is not a statistical sample of the Egyptian market |

These sources provide market context only. Generated records remain invented. No real social accounts, profile handles, photos, captions, comments, email addresses, phone numbers, or network identifiers are imported.

## How the synthetic context is constructed

- **Geography:** 27 governorates and a curated list of Egyptian cities and areas. Governorate population is weighted by (0.65 + 0.35 × CAPMAS urban share) as a transparent urban-creator prior. The 0.35 factor is a modelling assumption, not an observed platform statistic, and the resulting sample does not estimate any platform's real audience. Run a sensitivity comparison against simple population-only weighting before drawing conclusions.
- **Language:** Arabic and English bios, captions, comments, collection descriptions, and notifications. The 78% Arabic / 22% English split for local profiles is a modelling assumption, not a published statistic about social-media language.
- **Content:** bilingual examples for Egyptian food and cafés, street photography, crafts and furniture, local creative businesses, heritage, nature and coast, art/design, and learning/technology. They are synthetic examples, not observed Egyptian user-generated text.
- **Names and contact fields:** fictional names and reserved .test email/portfolio domains. Names are not records of identified people. Never replace the reserved domains with real contact domains.
- **Places:** governorate capitals use approximate city-centre reference coordinates. Fine-grained areas without a verified coordinate intentionally retain null latitude/longitude rather than fabricated precision.
- **Optional fields:** bios, disclosed locations, and websites are absent for some profiles. This natural missingness is distinct from the optional raw-quality profile, which injects a small, reproducible amount of Bronze data-quality noise after semantic validation.
- **Relationships and timing:** primary keys, foreign keys, account/profile ownership, post chronology, media/post type and event links must continue to pass the project validators.

## Assumptions to tune deliberately

Edit `config/egypt_market_profile.json` to change the simulation assumptions used by the generator. The module validates probability values and requires each language-mix weight set to sum to 1 before generation begins. The configuration is version-controlled so a particular output can be reproduced against the same scenario definition.

The generator records the active profile ID, configuration path, and resolved assumptions in `metadata/data_quality_report.json` under `egypt_market_context`:

- Arabic-versus-English mix for local, federated, and editorial/demo content.
- The urban-propensity factor used with CAPMAS population counts to weight governorate selection.
- Creator-cohort size and the higher probability of bios/websites in that cohort.
- Whether a profile discloses a public location and how often posts carry an explicit place tag.
- Topic stickiness, caption/comment follow-ups, and simple profile-layout/category assumptions.

All of these are scenario controls, not facts about PixelFed or Egyptian platform users. Change one assumption at a time, retain a fixed seed, and compare sensitivity runs before interpreting a KPI.

Do not tune the parameters simply to make a dashboard look convincing. Document hypotheses first, use a fixed seed, compare sensitivity runs, and label reports **synthetic scenario**. A population-weighted governorate mix is not a validated user-audience estimate.

## Making generated data more plausible

1. **Vary choices without forcing completeness.** Optional bios, websites, and locations should be missing for plausible reasons; not every account needs every event type.
2. **Use causality.** Likes, comments, bookmarks and reports follow their target post. Story views occur within story lifetime. Profile ownership and bridge tables reconcile.
3. **Use heterogeneous activity.** A small creator cohort may be active, casual accounts post occasionally, and some accounts have no posts in a given window. These remain stated simulation assumptions until suitable platform-level evidence exists.
4. **Make text contextual, not identical.** Combine themes, place labels, languages, and formats. Do not call template text scraped or real user content.
5. **Avoid false precision.** Use known governorate/city reference points where appropriate. Do not fabricate neighborhood coordinates.
6. **Version the evidence.** Record generator version, seed, as-of timestamp, reference dates, source URLs, and assumption configuration on every run.

## Public-source references

- CAPMAS, *Population Estimates By Governorate (Urban/Rural) 1/1/2024*: https://www.capmas.gov.eg/Admin/Pages%20Files/20245121324361-%20pop_new.pdf
- World Bank, *Individuals using the Internet (% of population) — Egypt, Arab Rep.*, indicator IT.NET.USER.ZS: https://data.worldbank.org/indicator/IT.NET.USER.ZS?locations=EG
- DataReportal / Kepios, *Digital 2026: Egypt*: https://datareportal.com/reports/digital-2026-egypt


## Executable engagement implementation

The [Egypt source → Silver → galaxy implementation](egypt-engagement-implementation.md) specifies the current executable build, timestamp/identity validation, exact grains, quarantine behavior and Power BI relationship plan. Existing manual guides remain reference workflows; the new JSONL build does not automatically migrate the saved Power BI model.
