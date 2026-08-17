# Naver Ads Playbook

## API 발급

네이버 검색광고 API는 공식 문서 기준으로 광고센터에서 발급합니다.

1. 네이버 검색광고 계정 로그인
2. 광고관리 시스템 접속
3. `도구 > API Manager`
4. `API License` 발급

공식 참고:
- `naver/searchad-apidoc` README
- Python sample의 인증 헤더 규격

## 환경변수

루트 `.env`에 아래 값을 넣습니다.

```env
NAVER_ADS_ACCESS_LICENSE=
NAVER_ADS_SECRET_KEY=
NAVER_ADS_CUSTOMER_ID=
NAVER_ADS_BASE_URL=https://api.searchad.naver.com
NAVER_ADS_DEFAULT_LANDING_URL=https://tiresiasview.com
```

## 스크립트

```bash
npm run naver:ads:check
npm run naver:ads:plan
npm run naver:ads:campaigns
npm run naver:ads:estimate -- --keywords "정책 시뮬레이션,시장 반응 예측" --bid 1500
```

## 초기 구조

- 브랜드 방어: `NAVER Powerlink | Brand | Tiresias View`
- 문제 해결형 검색: `NAVER Powerlink | Solution Intent | Tiresias View`

핵심 광고군:
- 정책 시뮬레이션
- 시장 반응 예측
- 여론 반응 시뮬레이션

## 운영 원칙

- 브랜드검색보다 파워링크부터 시작
- 광고 문구는 `보고서 업로드 -> 시나리오 비교 -> 분석 보고서 생성` 흐름을 반복
- 무료/과제/채용 의도는 제외 키워드로 관리
