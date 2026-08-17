# Tiresias View

문서 기반 정책·시장·여론 시뮬레이션 서비스입니다.

- 문서를 업로드하면 온톨로지와 지식 그래프를 만듭니다.
- 그래프를 바탕으로 페르소나와 시뮬레이션 환경을 구성합니다.
- 시뮬레이션 결과를 보고서와 PDF로 정리합니다.

## 저장소 구성

- `frontend/`: Vue 클라이언트
- `workers/`: Cloudflare Worker, D1, R2, 인증/결제/큐/백엔드 프록시
- `backend/`: Flask API, 그래프/시뮬레이션/보고서 처리, PDF 렌더링

## 시작

```bash
cp .env.example .env
npm run setup:all
npm run dev
```

- 프런트엔드 로컬 개발 서버: `http://localhost:5173`
- 백엔드 로컬 API: `http://localhost:5001`

## 추가 문서

- 한국어 가이드: [README-KO.md](./README-KO.md)
- English guide: [README-EN.md](./README-EN.md)
- Google Ads 운영 문서: [docs/marketing/google-ads-playbook.md](./docs/marketing/google-ads-playbook.md)
- 원저작권 및 변경 고지: [NOTICE.md](./NOTICE.md)
