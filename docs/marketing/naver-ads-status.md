# Naver Ads Status

## Current

- Repo에 네이버 검색광고 API 스크립트 뼈대 추가
- 공식 인증 헤더 규격 반영
- 초기 캠페인/키워드 초안 추가
- 실제 API 호출은 계정의 `API License`, `Secret Key`, `Customer ID` 필요
- `scripts/naver-ads/sync-search-campaign.mjs` 추가
- 실제 캠페인 생성 완료
  - `TV | Brand | 70won` (`cmp-a001-01-000000010432964`)
  - `TV | High Intent | 70won` (`cmp-a001-01-000000010432965`)
- 광고그룹 생성 완료
  - `Brand Core` (`grp-a001-01-000000064424009`)
  - `Scenario Analysis` (`grp-a001-01-000000064424010`)
- 소재(TEXT_45) 6개 생성 완료, 현재 `ELIGIBLE/APPROVED`
- 키워드 11개 생성 완료, 현재 `UNDER_REVIEW`
- 네이버 키워드는 공백 포함 키워드가 `3906 Invalid characters`로 거절될 수 있어, 현재 운영 세트는 공백 없는 형태로 구성

## Required credentials

- `NAVER_ADS_ACCESS_LICENSE`
- `NAVER_ADS_SECRET_KEY`
- `NAVER_ADS_CUSTOMER_ID`
