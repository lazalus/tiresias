# MiroFish 한국어 요약

## 이 프로젝트가 뭔가

MiroFish는 멀티 에이전트 기반 예측 시뮬레이션 웹앱입니다.

- 뉴스, 정책, 금융 신호, 보고서, 소설 같은 문서를 넣습니다.
- 시스템이 문서에서 개체와 관계를 뽑아 그래프를 만듭니다.
- 그 그래프를 바탕으로 여러 Agent의 성격, 기억, 행동 규칙을 생성합니다.
- 이후 시뮬레이션을 돌려 결과를 분석 리포트로 반환합니다.
- 마지막에는 시뮬레이션 세계의 Agent나 보고서 Agent와 대화할 수 있습니다.

README 기준 핵심 메시지는 "현실의 씨앗 정보를 넣으면 디지털 평행 세계를 만들어 미래 흐름을 예측한다"입니다.

## 전체 흐름

1. 문서 업로드
2. GraphRAG 기반 그래프 구성
3. Agent 프로필 및 시뮬레이션 환경 생성
4. Twitter/Reddit 스타일 병렬 시뮬레이션 실행
5. 리포트 생성 및 상호작용

## 기술 스택

- 프론트엔드: Vue 3 + Vite + axios + d3
- 백엔드: Flask
- LLM 연동: OpenAI SDK 호환 API
- 메모리/그래프: Zep Cloud
- 시뮬레이션 엔진: CAMEL OASIS

## 주요 폴더

- `frontend/`: 화면과 사용자 흐름
- `backend/app/api/`: API 엔드포인트
- `backend/app/services/`: 그래프 생성, 프로필 생성, 리포트 생성, 시뮬레이션 실행 로직
- `backend/scripts/`: 실제 시뮬레이션 실행 스크립트
- `static/`: README용 이미지와 정적 자산

## 실행 조건

- Node.js 18+
- Python 3.11 ~ 3.12
- `uv`
- `.env`에 LLM API 키와 Zep API 키 필요

## 빠른 실행

```bash
cp .env.example .env
npm run setup:all
npm run dev
```

- 프론트: `http://localhost:3000`
- 백엔드: `http://localhost:5001`

## 꼭 알아둘 점

- 기본 문서는 중국어 `README.md`, 영어 문서는 `README-EN.md`입니다.
- 이 프로젝트는 외부 LLM API와 Zep Cloud를 사용하므로, 인터넷이 되는 환경과 유효한 API 키가 필요합니다.
- 업로드 가능한 파일 형식은 `pdf`, `md`, `markdown`, `txt`입니다.

## 이번에 확인한 보안 메모

코드 기준으로 즉시 실행되는 악성 스크립트, 숨겨진 마이너, 원격 쉘 생성 코드는 보이지 않았습니다. 다만 원본 저장소는 개발 편의 위주 설정이 섞여 있어서, 현재 워크스페이스에는 아래 방향으로 조정했습니다.

- CORS 기본값을 로컬 개발 주소로 제한
- `FLASK_DEBUG` 기본값을 `false` 기준으로 사용
- API 에러 응답에서 traceback을 기본 비노출 처리
- 로그 레벨을 환경변수로 제어 가능하게 정리

추가로 실제 운영 전에 해야 할 일은 인증 추가, 업로드 제한 강화, API rate limit 적용입니다.
