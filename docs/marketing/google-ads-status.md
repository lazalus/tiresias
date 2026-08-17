# Google Ads Status

Last updated: 2026-03-21

## Confirmed account IDs

- Customer account ID: `8165943772`
- Manager account ID: `5481736491`

## Repo work completed

- Google Ads API scaffolding added under `scripts/google-ads/`
- Search campaign blueprints created for:
  - brand search
  - solution-intent search
- Conversion action creation script added:
  - `scripts/google-ads/create-conversion-actions.mjs`
- Reporting and offline conversion upload scripts added
- Frontend Google tag bootstrap added in `frontend/src/utils/marketing.js`
- Frontend conversion events connected:
  - signup complete
  - quote requested
  - purchase completed

## Current blocker

- Google Ads API production calls are blocked by:
  - `DEVELOPER_TOKEN_NOT_APPROVED`
- Meaning:
  - OAuth is set up
  - config loading works
  - the developer token is not yet approved for non-test accounts

## What still requires Google-side manual work

1. Wait for or complete Google developer token approval.
2. In Google Ads UI, create conversion actions for:
   - `signup_complete`
   - `quote_requested`
   - `purchase_completed`
3. Put the resulting Google Ads conversion labels into frontend env:
   - `VITE_GOOGLE_ADS_SIGNUP_LABEL`
   - `VITE_GOOGLE_ADS_QUOTE_LABEL`
   - `VITE_GOOGLE_ADS_PURCHASE_LABEL`

## First commands to run after approval

```bash
npm run ads:check
npm run ads:plan
npm run ads:campaign:sync -- --apply
npm run ads:report:search-terms -- --days 14
```

## Important security note

- Google Ads client secret and refresh token were exposed during setup conversation.
- Rotate them after setup stabilizes.
