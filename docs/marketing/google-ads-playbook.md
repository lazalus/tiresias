# Google Ads Playbook

This repo now contains a minimal Google Ads operating scaffold for Tiresias.

## What is in the repo

- API tooling:
  - `scripts/google-ads/validate-config.mjs`
  - `scripts/google-ads/generate-plan.mjs`
  - `scripts/google-ads/sync-search-campaign.mjs`
  - `scripts/google-ads/fetch-search-terms.mjs`
  - `scripts/google-ads/upload-offline-conversions.mjs`
- Campaign blueprints:
  - `scripts/google-ads/data/solution-search.kr.json`
  - `scripts/google-ads/data/brand-search.kr.json`
  - `scripts/google-ads/data/negative-keywords.kr.json`
- Frontend tracking helper:
  - `frontend/src/utils/marketing.js`
- Frontend env template:
  - `frontend/.env.example`

## Credentials and config

Populate the root `.env` with:

- `GOOGLE_ADS_CUSTOMER_ID`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- optional `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
- optional `GOOGLE_ADS_API_VERSION`
- optional `GOOGLE_ADS_DEFAULT_LANDING_URL`

Populate `frontend/.env` with:

- `VITE_GOOGLE_TAG_ID`
- optional `VITE_GA_MEASUREMENT_ID`
- optional `VITE_GOOGLE_ADS_ID`
- optional conversion labels:
  - `VITE_GOOGLE_ADS_SIGNUP_LABEL`
  - `VITE_GOOGLE_ADS_QUOTE_LABEL`
  - `VITE_GOOGLE_ADS_PURCHASE_LABEL`

## NPM commands

```bash
npm run ads:check
npm run ads:plan
npm run ads:conversions:create
npm run ads:conversions:create -- --apply
npm run ads:campaign:sync
npm run ads:campaign:sync -- --apply
npm run ads:report:search-terms -- --days 14
npm run ads:conversions:upload -- --file path/to/conversions.json
```

`ads:campaign:sync` is safe by default.
Only `--apply` performs mutations.

## Recommended launch structure

Start with two search campaigns:

1. `KR Search | Solution Intent | Tiresias`
- Goal: capture high-intent non-brand demand
- Budget: `50,000 KRW/day`
- Bidding: start with `MAXIMIZE_CLICKS`
- Switch to `MAXIMIZE_CONVERSIONS` after stable conversion volume

2. `KR Search | Brand | Tiresias`
- Goal: defend brand traffic and increase branded conversion efficiency
- Budget: `15,000 KRW/day`
- Bidding: `MAXIMIZE_CLICKS`

Do not start with broad display/video before search terms and conversion quality are stable.

## Initial ad group strategy

Solution campaign:

- `Scenario Analysis`
- `Policy Simulation`
- `Market Response`
- `Public Opinion`

Brand campaign:

- `Brand Core`

The repo blueprints already include starter keywords and responsive search ad assets.

## Keyword logic

Keep the first wave focused on pain + use case:

- scenario analysis
- policy impact simulation
- market response prediction
- public opinion analysis
- stakeholder response analysis

Avoid broad research-intent traffic at launch.
The starter negative list removes obvious low-intent terms such as free, wiki, assignment, template, and job search terms.

## Conversion design

Use one primary conversion and two secondary conversions.

Primary:

- `purchase_completed`
  - definition: confirmed paid simulation order
  - source of truth: backend / Worker payment confirmation

Secondary:

- `signup_complete`
  - definition: successful account creation
- `quote_requested`
  - definition: user receives estimate after uploading files and entering a topic

Optional later:

- `sample_report_view`
- `pdf_purchase_completed`
- `demo_request_submitted`

## Tracking flow

### Online conversions

The frontend helper in `frontend/src/utils/marketing.js` does three things:

- loads `gtag.js` when a tag ID exists
- captures `gclid`, `gbraid`, `wbraid`, and UTM params into local storage
- provides:
  - `trackPageView()`
  - `trackMarketingEvent()`
  - `trackGoogleAdsConversion()`

Recommended call points:

- signup success:
  - fire `trackGoogleAdsConversion('signup_complete')`
- estimate success in `Home.vue`:
  - fire `trackGoogleAdsConversion('quote_requested')`
- confirmed payment success:
  - fire `trackGoogleAdsConversion('purchase_completed', { value, currency: 'KRW' })`

### Offline / imported conversions

For reliable paid conversion attribution, import click-based conversions from authoritative payment events.

Recommended flow:

1. Capture `gclid`, `gbraid`, `wbraid` on landing.
2. Persist the latest click IDs locally.
3. On signup, estimate, or payment creation, send those click IDs to Worker/backend and store them with the user or order record.
4. On confirmed payment, export a conversion row and upload via `ads:conversions:upload`.

Example conversion import file:

```json
[
  {
    "conversionActionName": "purchase_completed",
    "conversionDateTime": "2026-03-21 18:45:00+09:00",
    "conversionValue": 17900,
    "currencyCode": "KRW",
    "orderId": "payorder_123",
    "gclid": "EAIaIQob..."
  }
]
```

## Operational flow for this product

Week 1:

- launch brand + solution search campaigns
- keep both paused until conversion tag QA is complete
- verify:
  - tag load
  - page view firing
  - signup conversion
  - quote conversion
  - purchase conversion

Week 2:

- review search terms daily
- add negatives aggressively
- split out strong themes into dedicated ad groups
- keep low-volume exploratory keywords paused if CTR and landing quality are weak

After 15-30 real primary conversions:

- switch non-brand campaign from `MAXIMIZE_CLICKS` to `MAXIMIZE_CONVERSIONS`
- separate best-converting use case into a dedicated campaign

## Repo follow-up still needed

The frontend helper is installed globally, but event calls are not yet wired into the actual signup / estimate / payment success handlers.

The next integration pass should:

- call `trackGoogleAdsConversion('signup_complete')` after signup success
- call `trackGoogleAdsConversion('quote_requested')` after estimate success
- call `trackGoogleAdsConversion('purchase_completed')` after confirmed payment success
- store click IDs with user/order records so offline imports can use authoritative payment data
