# Tiresias View 한국어 가이드

## 서비스 개요

Tiresias View는 문서 기반 정책·시장·여론 시뮬레이션 서비스입니다.

- 사용자가 PDF, Markdown, TXT 문서를 업로드합니다.
- 시스템이 문서에서 온톨로지와 지식 그래프를 구성합니다.
- 그래프를 바탕으로 페르소나와 시뮬레이션 환경을 준비합니다.
- 시뮬레이션 결과를 분석해 보고서와 PDF를 생성합니다.
- 완료된 보고서는 히스토리에서 다시 조회하고 다운로드할 수 있습니다.

## 현재 구조

- `frontend/`: Vue 3 + Vite 클라이언트
- `workers/`: Cloudflare Worker, D1, R2, 결제/인증/큐 처리
- `backend/`: Flask 기반 그래프/시뮬레이션/보고서 API

현재 운영 구조는 다음과 같습니다.

- 프런트엔드와 Worker는 이 저장소에서 배포합니다.
- Worker가 public `/api/*` 진입점 역할을 합니다.
- Worker의 무거운 작업 프록시 대상 백엔드 기본 URL은 `https://api.tiresiasview.com` 입니다.
- 백엔드의 실제 호스트 머신이나 서버 경로는 이 저장소에서 고정하지 않습니다.
- 그래프 저장소는 Neo4j 기준으로 구성되어 있습니다.
- LLM 호출은 OpenAI 호환 API 기준으로 구성되어 있습니다.
- 보고서 PDF는 백엔드의 Node + Playwright 렌더러를 사용합니다.

## 로컬 실행

```bash
cp .env.example .env
npm run setup:all
npm run dev
```

- 프런트엔드: `http://localhost:5173`
- 백엔드 API: `http://localhost:5001`

개별 실행:

```bash
npm run frontend
npm run backend
```

## 배포

프런트엔드 + Worker:

```bash
npm run deploy
```

원격 D1 migration:

```bash
cd workers
npx wrangler d1 migrations apply tiresias-db --remote
```

백엔드 배포와 재시작은 이 저장소 밖에서 관리합니다.
호스트 종류나 서버 경로를 README에 고정하지 않습니다.

## 운영 메모

- 결제는 Toss Payments를 사용합니다.
- 보고서 PDF는 R2 캐시와 백엔드 공용 렌더러를 함께 사용합니다.
- 무거운 작업은 Worker 대기열을 통해 순번 기반으로 처리합니다.
- 현재 서비스명 기준 기술 식별자는 `tiresias` 슬러그를 사용합니다.
- 워커는 `/api/graph`, `/api/simulation`, `/api/report` 계열을 내부 키와 함께 백엔드로 프록시합니다.

## 추가 문서

- 영어 문서: [README-EN.md](./README-EN.md)
- Google Ads 운영 문서: [docs/marketing/google-ads-playbook.md](./docs/marketing/google-ads-playbook.md)
- 원저작권/변경 고지: [NOTICE.md](./NOTICE.md)
