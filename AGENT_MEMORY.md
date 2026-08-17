# AGENT_MEMORY

Last updated: 2026-03-22

This file is the short operational memory for this repo.
Do not store secrets here.

## Ground truth rule

- Prefer code and deployed endpoint configuration over README text.
- Do not assume a specific physical host from old notes.
- The repo shows the backend public base URL, but not the underlying server path or machine layout.

## Project layout

- `frontend/`: Vue 3 + Vite client
- `workers/`: Cloudflare Worker + D1 + R2 + auth/payments/queue/proxy
- `backend/`: Flask API for graph build, simulation, report generation, and PDF rendering

## Current runtime topology

- Frontend and Worker are deployed from this repo.
- The Worker serves the built frontend assets and the public `/api/*` entrypoint.
- Worker public URL:
  - `https://tiresias-api.nov9306-564.workers.dev`
- Worker proxies heavy backend routes to the backend base URL configured as `SIMULATION_API`.
  - current configured value in `workers/wrangler.toml`: `https://api.tiresiasview.com`
- Do not assume the host behind `https://api.tiresiasview.com` is a Mac mini or any other specific server unless verified outside this repo.
- Backend entrypoints in repo:
  - local/dev: `backend/run.py`
  - production-style WSGI: `backend/wsgi.py`
- Worker adds `X-Internal-Key` when proxying backend routes.
- Backend rejects `/api/*` requests without the internal key when `INTERNAL_API_KEY` is configured.

## Public API split

- Worker handles directly:
  - `/api/auth`
  - `/api/admin`
  - `/api/payments`
  - `/api/projects`
  - `/api/files`
  - `/api/reports`
  - `/api/queue`
  - `/api/estimate`
  - `/api/report/pdf/:reportId`
- Worker proxies to backend:
  - `/api/graph/*`
  - `/api/simulation/*`
  - `/api/report/*`

## Data and infra expectations

- User/account/project/payment/report metadata lives in Worker-side D1/R2.
- Graph storage expected by backend config is Neo4j.
- Runtime simulation files are backend-local state.
- Report PDF rendering is backend-side and uses Node + Playwright.
  - renderer service: `backend/app/services/report_pdf_renderer.py`
  - render script: `backend/scripts/render_report_pdf.mjs`

## Deployment notes

- Frontend + Worker deploy:
  - `npm run deploy`
- Remote D1 migrations:
  - `cd workers && npx wrangler d1 migrations apply tiresias-db --remote`
- Local D1 migrations:
  - `npm run db:migrate:local`
- Backend deployment/restart is external to this repo.
- Do not write host-specific deployment instructions here unless they are re-verified.

## Backend config that matters

- LLM:
  - `LLM_API_KEY` or `OPENAI_API_KEY`
  - `LLM_BASE_URL` / `OPENAI_BASE_URL`
  - `LLM_MODEL_NAME` / `OPENAI_MODEL_NAME`
  - `OPENAI_ADMIN_KEY`
- Backend auth / CORS:
  - `INTERNAL_API_KEY`
  - `CORS_ALLOWED_ORIGINS`
- Graph:
  - `GRAPH_BACKEND=neo4j`
  - `NEO4J_URI`
  - `NEO4J_USERNAME`
  - `NEO4J_PASSWORD`
  - `NEO4J_DATABASE`
- Capacity guard:
  - `CAPACITY_RETRY_AFTER_SECONDS`
  - `MAX_CONCURRENT_HEAVY_JOBS`
  - `MAX_CONCURRENT_PREPARES`
  - `MAX_CONCURRENT_GRAPH_BUILDS`
  - `MAX_CONCURRENT_REPORTS`
  - `MAX_CONCURRENT_RUNNING_SIMULATIONS`
  - `MAX_CONCURRENT_SIMULATION_ENVS`

## Worker config that matters

- `SIMULATION_API`
- `INTERNAL_API_KEY`
- `OPENAI_ADMIN_KEY`
- D1 binding: `DB`
- R2 binding: `STORAGE`
- AI binding: `AI`

## Current product flow

- User uploads files in the frontend.
- Frontend stages pending uploads before requesting `/api/estimate`.
- Worker can call backend `/api/graph/preanalysis` for a cheap estimate-time preanalysis pass.
- Worker creates/updates project records and payment orders in D1.
- Heavy jobs are queued in Worker `job_queue`.
- Backend performs graph build, simulation prep/run, and report generation.
- Report PDFs are rendered in backend and cached through Worker/R2.

## Google Ads status

- Repo-side Google Ads integration scaffold exists.
  - scripts: `scripts/google-ads/*`
  - campaign blueprints: `scripts/google-ads/data/*`
  - playbook: `docs/marketing/google-ads-playbook.md`
- Frontend tracking helper is installed and initialized.
  - file: `frontend/src/utils/marketing.js`
  - initialized from: `frontend/src/main.js`
- Online conversion events are wired at:
  - signup success: `frontend/src/views/Signup.vue`
  - quote/estimate success: `frontend/src/views/Home.vue`
  - payment success: `frontend/src/views/Credits.vue`
- Current Google Ads identifiers confirmed:
  - customer account id: `8165943772`
  - manager account id / login customer id: `5481736491`
- OAuth client and refresh token were obtained manually outside repo.
- Sensitive Google Ads credentials belong only in `.env`, never in `.env.example` or committed docs.
- Current blocker:
  - Google Ads API returns `DEVELOPER_TOKEN_NOT_APPROVED`
  - meaning the developer token is still limited to test accounts and cannot access production ad accounts yet
- Re-verified on 2026-03-24 with `npm run ads:campaign:sync`:
  - env/config loads correctly for customer `8165943772` and login customer `5481736491`
  - live Google Ads search call still fails with `403 PERMISSION_DENIED`
  - Google Ads authorization error remains `DEVELOPER_TOKEN_NOT_APPROVED`
- Until the developer token is approved, repo-side scripts can be prepared and validated, but real campaign mutation/report calls against production accounts will fail.
- After approval, first actions:
  - create Google Ads conversion actions and copy labels into frontend env
  - run `npm run ads:check`
  - run search campaign sync with `--apply`
  - validate search-term reporting and conversion attribution

## Naver Ads status

- Repo-side Naver Search Ads integration scaffold exists.
  - scripts: `scripts/naver-ads/*`
  - campaign blueprints: `scripts/naver-ads/data/*`
  - playbook/status: `docs/marketing/naver-ads-playbook.md`, `docs/marketing/naver-ads-status.md`
- Official Naver Search Ads API spec re-check on 2026-03-24 showed campaign/adgroup/ad creation requests require the expected create payload shape; the earlier mutation failure was not an account-wide write-permission issue.
- Practical fix applied in repo:
  - Naver create helpers now include `customerId` on campaign/adgroup/ad creation in `scripts/naver-ads/lib/client.mjs`
  - sync script added at `scripts/naver-ads/sync-search-campaign.mjs`
  - current launch strategy uses only low-cost brand + high-intent search sets with `70` KRW bid and tight daily budgets
- Confirmed approved Tiresias business channel:
  - `bsn-a001-00-000000013810169`
  - channel key: `https://tiresiasview.com`
  - status: `ELIGIBLE`
- Live campaigns created on 2026-03-24:
  - `TV | Brand | 70won` (`cmp-a001-01-000000010432964`)
  - `TV | High Intent | 70won` (`cmp-a001-01-000000010432965`)
- Live ad groups created:
  - `Brand Core` (`grp-a001-01-000000064424009`)
  - `Scenario Analysis` (`grp-a001-01-000000064424010`)
- Text ads were created successfully and are currently `APPROVED` / `ELIGIBLE`.
- Keywords were created successfully and are currently under review; until review completes they can appear as `PAUSED` with `KEYWORD_UNDER_REVIEW`.
- Important keyword caveat observed in practice:
  - Naver can reject keywords containing spaces with `3906 Invalid characters are included in the keyword`
  - current operating sets therefore use compact no-space forms such as `정책시뮬레이션`, `시장반응예측`, `테이레시아스뷰`

## Important implemented behavior

- Scanned/image PDF OCR fallback exists in `backend/app/utils/file_parser.py`.
- Graph build re-extracts project files when stored text is too small.
- Graph build treats `0 nodes / 0 edges` as failure, not success.
- Graph extraction now uses a 2-stage pipeline in `backend/app/services/graph_builder.py`.
- Korean canonical entity normalization no longer collapses distinct Hangul names into one key.
- Simulation memory compaction exists for report/search flow.
- Backend overload guardrails exist in `backend/app/services/capacity_guard.py`.
- Worker-side fair queue exists in `workers/src/queue.js`.
- Report search accepts `scope` and falls back from edge-only to node+edge search when needed.
- PDF download payment enforcement exists on the Worker side.

## Known caveats

- Graph relation quality can still degrade on long PDFs.
- Graph build is still synchronous enough to feel slow on larger inputs.
- Direct backend calls can still return `429`; the intended user path is through the Worker queue.
- Failed project recovery is better when a `graph_id` already exists than when failure happens earlier.
- There is still no universal user-facing retry path for every failure state.
- Verified on 2026-03-22:
  - the current public backend health endpoint can still return `200 OK` while Gunicorn workers are unstable underneath
  - remote launchd is now running Gunicorn on macOS with `--workers 1 --worker-class gthread`
  - remote stderr shows repeated worker crashes with macOS Objective-C fork errors:
    - `+[NSCharacterSet initialize] may have been in progress in another thread when fork() was called`
  - the local code path most likely involved is the Darwin-only OCR fallback in `backend/app/utils/file_parser.py`, backed by `ocrmac` in `backend/pyproject.toml`
  - practical effect: heavy PDF / ontology requests can fail intermittently even though `/health` looks healthy
- immediate runtime hotfix applied on remote launch agent:
  - changed Gunicorn workers from `2` to `1`
  - added `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`
  - reloaded `~/Library/LaunchAgents/com.tires.backend.plist`
- additional runtime fix applied on 2026-03-22:
  - removed Gunicorn `--max-requests` and `--max-requests-jitter` from remote launchd config
  - reason: worker auto-recycle was killing in-process background report generation threads and surfacing as "백엔드 재시작으로 중단"
- verified on 2026-03-25:
  - macmini backend is still running outside Docker via `uv run gunicorn`
  - Neo4j on macmini is running inside Docker as container `mirofish-neo4j`
  - backend `.env` points to that local container via `NEO4J_URI=bolt://127.0.0.1:7687`
  - Neo4j data is stored on host bind mounts under `~/neo4j/{data,logs,import,plugins}`, not in Docker volumes
  - Neo4j container was migrated from `amd64` emulation to native `arm64`
  - pre-migration graph counts: `5625` nodes, `5997` relationships
  - post-migration graph counts were verified identical, and backend `/health` remained `ok`
- admin OpenAI cost stats changed on 2026-03-22:
  - Worker `/api/admin/openai-costs` now reads from D1 cache table `openai_cost_cache` first
  - if cached data exists, admin UI keeps showing the last stored snapshot immediately
  - stale cache refresh now runs in the background via Worker `waitUntil`
  - only the first miss for a given `days` window falls back to live backend fetch
- code-side recovery patch deployed on 2026-03-22:
  - backend startup now marks interrupted `graph_building` projects as `failed`
  - backend startup now marks interrupted report states (`pending` / `planning` / `generating`) as `failed`
  - report generation now persists a placeholder report/progress record before background work starts
  - report UI now polls `/api/report/<report_id>/progress`, shows a failure state, and routes users back to retry from the simulation workspace
  - graph polling UI now handles missing in-memory task ids after backend restart by reloading project state instead of hanging silently
  - simulation workspace re-entry no longer auto-restarts Step2 prepare before project/report status is loaded
  - `report_generating` / `report_completed` projects now block Step2 auto-prepare and redirect cleanly back to report flow instead of blinking on agent-profile generation
  - Worker project reads now reconcile stale D1 `report_generating` state against backend report status before returning project state
  - graph rendering now retries when the panel first mounted hidden at `0px` width and rerenders when the graph tab becomes visible
- PDF template has been moved toward a Korean public-institution report style: minimal cover, centered formal title, dedicated TOC page, restrained blue/teal section bands
- SEO/public-page update deployed on 2026-03-24:
  - new public pricing page at `/pricing`
  - landing page now links internally to `/features`, `/pricing`, `/samples`, `/support`
  - landing structured data now includes `Organization` in addition to app/FAQ data
  - sample list/detail pages now set page-specific SEO meta and structured data (`CollectionPage`, `ItemList`, `Report`)
  - `/terms`, `/privacy`, `/open-source` now set explicit SEO meta
  - `/login`, `/signup`, `/signup/verify` now set `noindex,follow`
  - dynamic sitemap now includes `/pricing`
  - deployed Worker/frontend version: `3b047fea-4eae-441f-8f9b-689564054d5d`

## Canonical D1 project statuses

- `created`
- `ontology_generated`
- `graph_building`
- `graph_completed`
- `simulation_preparing`
- `simulation_ready`
- `simulation_running`
- `simulation_completed`
- `report_generating`
- `report_completed`
- `failed`
- `simulation_stopped`

## Files to read first for ops/runtime changes

- Frontend:
  - `frontend/src/views/Home.vue`
  - `frontend/src/views/MainView.vue`
  - `frontend/src/store/pendingUpload.js`
- Worker:
  - `workers/src/index.js`
  - `workers/src/projects.js`
  - `workers/src/payments.js`
  - `workers/src/reports.js`
  - `workers/src/queue.js`
  - `workers/src/utils.js`
- Backend:
  - `backend/app/__init__.py`
  - `backend/app/config.py`
  - `backend/app/api/graph.py`
  - `backend/app/api/simulation.py`
  - `backend/app/api/report.py`
  - `backend/app/api/admin.py`
  - `backend/app/services/graph_builder.py`
  - `backend/app/services/neo4j_graph_store.py`
  - `backend/app/services/simulation_manager.py`
  - `backend/app/services/simulation_runner.py`
  - `backend/app/services/report_pdf_renderer.py`
  - `backend/app/utils/file_parser.py`
  - `backend/app/utils/llm_client.py`

## Rule for future work

- Before changing deployment, runtime, auth, queue, payment, graph, or report behavior, read this file first and verify against current code.

## Recent updates

- OpenAI 비용 조회는 Worker가 D1 `openai_cost_cache`를 먼저 반환하고, 오래된 경우에만 백그라운드 갱신한다. live fetch 실패 시 기존 캐시를 유지한다.
- 회원가입은 `pending signup -> Resend 인증 메일 -> 링크 확인 -> 실제 users 생성` 구조로 변경했다.
- 원격 D1 마이그레이션 `0008_add_signup_verifications.sql` 적용 완료.
- 해당 프론트/Worker 코드는 배포 완료 (`10bdb640-2743-45f0-85cc-d950d63838f6`).
- Cloudflare Worker에는 기본 var(`RESEND_FROM_EMAIL`, `RESEND_FROM_NAME`, `AUTH_BASE_URL`, `SUPPORT_EMAIL`, `AUTH_SIGNUP_VERIFICATION_TTL_HOURS`)와 secret `AUTH_SIGNUP_VERIFICATION_SECRET`를 반영했다.
- `RESEND_API_KEY`도 Cloudflare Worker secret에 반영 완료.
- 스모크 테스트 `/api/auth/signup` 결과는 `200 {"success":true,"pending":true,...}` 로 통과했다.
- 테스트용 pending signup(`codex-resend-check@example.com`)은 원격 D1에서 정리했다.
- 네이버 검색광고 API용 스크립트 뼈대를 `scripts/naver-ads` 아래에 추가했다.
- 준비된 명령: `npm run naver:ads:check`, `npm run naver:ads:plan`, `npm run naver:ads:campaigns`, `npm run naver:ads:estimate`.
- 필요한 자격증명: `NAVER_ADS_ACCESS_LICENSE`, `NAVER_ADS_SECRET_KEY`, `NAVER_ADS_CUSTOMER_ID`.
- 운영 문서: `docs/marketing/naver-ads-playbook.md`, `docs/marketing/naver-ads-status.md`.
- 고객센터 페이지(`frontend/src/views/Support.vue`)에 `고객 의견` 폼을 추가했다.
- 의견 유형은 `문의하기`, `불편사항 접수`, `서비스 개선 제안` 3종이며, `POST /api/support/feedback`로 Worker에 전달된다.
- Worker `workers/src/support.js`가 Resend로 `support@tiresiasview.com` 에 메일을 보낸다.
- 배포 버전 `a4992064-79f6-4ea5-8b47-869307183b71` 에서 `/api/support/feedback` 스모크 테스트 `200` 확인.
- 관리자에 Search Console 진단 섹션을 추가했다. Worker가 `search_console_cache`를 D1에 저장하고, 검색어/페이지/CTR/평균순위/핵심 페이지 색인 상태를 캐시 우선으로 보여준다.
- Search Console용 Worker secret `GOOGLE_SEARCH_CONSOLE_CLIENT_ID`, `GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET`, `GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN` 을 설정했다.
- 새 Search Console refresh token으로 `sc-domain:tiresiasview.com` 조회와 Search Analytics 호출이 성공했다. 현재 최근 28일 기준 노출 3, 클릭 0 수준으로 데이터가 매우 적다.
- SEO 개선으로 랜딩에 FAQ 섹션과 FAQ/SoftwareApplication 구조화 데이터를 추가했고, `Features`/`Support` 페이지에 개별 meta/canonical 설정을 넣었다.
- Worker는 이제 `http://tiresiasview.com` 요청을 `https://tiresiasview.com` 으로 301 리다이렉트한다.
- 보안 하드닝 1차 적용: 마크다운 렌더는 `frontend/src/utils/markdown.js` 에서 HTML escape 후 렌더하도록 바꿨다. `v-html` 사용 지점은 공유 렌더러를 통하게 해 저장형 XSS 위험을 낮췄다.
- 인증은 localStorage 영구 토큰 대신 Worker의 `HttpOnly Secure SameSite=Lax` 쿠키(`tv_session`)를 기본 세션 경로로 사용한다. 프론트는 로그인 직후 메모리 토큰만 유지하고, 새로고침 후에는 `/api/auth/me` 로 쿠키 세션을 복구한다.
- Worker `workers/src/auth.js` 에 로그인/회원가입 rate limit을 추가했다. `auth_rate_limits` 테이블과 마이그레이션 `0011_add_auth_rate_limits.sql` 이 적용되어 IP/이메일 기준 과도한 시도를 `429` 와 `Retry-After` 로 차단한다.
- Worker `workers/src/index.js` 는 이제 CSP, `X-Frame-Options`, `Referrer-Policy`, `X-Content-Type-Options`, `Permissions-Policy` 를 모든 API 응답에 붙인다.
- CORS는 `*` 에서 배포 도메인/개발 도메인만 허용하는 동적 origin 방식으로 변경했다. 쿠키 세션과 맞도록 허용 origin 에만 `Access-Control-Allow-Credentials: true` 를 반환한다.
- Google 태그와 Google Analytics 요청이 막히지 않도록 CSP에 `www.googletagmanager.com`, `www.google-analytics.com`, `region1.google-analytics.com` 을 허용했다.
- 보안 하드닝 배포 버전은 `389148ef-22f0-488a-b807-6527ceae4638` 이다.
- 2026-03-24 스모크 테스트로 `로그인 -> pending upload -> ontology -> graph -> simulation create -> prepare -> start -> report generate` 전체를 실제 운영 도메인에서 검증했다.
- 스모크 테스트 산출물은 정리 완료. 테스트용 backend report `report_311fbec873fa`, project `proj_a151e061fc6f`, D1 임시 admin 유저 `codex-smoke-admin` 및 관련 queue/auth_rate_limits 레코드는 삭제했다.
- 스모크 테스트 중 `simulation_prepare` 대기열에 2026-03-22 생성된 stale `queued` 항목(`21f4ed1a-8b27-431c-a3c9-cfe045e0b82f`)이 남아 새 prepare 작업을 막는 운영 버그를 확인했고, 수동으로 `failed` 처리해 해소했다.
- 시뮬레이션 시작 시 `max_rounds=2` 요청이 실제로는 `max_rounds_applied=10` 으로 적용됐다. 최소 라운드 강제 또는 파라미터 무시 여부를 나중에 확인할 필요가 있다.
- `/api/report/<report_id>` 백엔드 보고서 조회는 정상적으로 완성 본문을 반환했지만, Worker 메타 저장소 `/api/reports` 및 `/api/reports/:id/refined` 에는 동일 보고서가 자동 반영되지 않았다. 백엔드 완료 후 Worker 저장 동기화는 프론트 의존 경로일 가능성이 있다.
- 이후 조치: Worker `queue.js` 에 1시간 이상 갱신되지 않은 `queued` 항목 자동 정리를 넣었다. 새 작업 생성, queue 상태 조회, queue 상태 계산 시 stale queued entry를 `failed` 로 정리한다.
- 이후 조치: Worker `reportState.js` / `reports.js` 에 백엔드 완료 보고서를 Worker D1/R2로 자동 미러링하는 경로를 추가했다. 이제 프로젝트/보고서 조회 시 프론트 후처리 없이도 `reports` 메타가 복구된다.
- 위 수정 배포 버전은 `f40e4ee3-3599-4232-89d6-e0b88a22e9e8` 이다.
- `max_rounds=2 -> 10` 현상은 전달 오류가 아니라 백엔드 정책이다. `backend/app/api/simulation.py` 와 `backend/app/services/simulation_config_generator.py` 가 최소 10 라운드를 강제한다.
- 프론트는 이에 맞춰 `Step2EnvSetup.vue`, `Step3Simulation.vue`, `SimulationRunView.vue` 에서 최소 10 라운드 하한을 명시하고, 실행 화면은 요청값이 아니라 실제 적용값(`max_rounds_applied`) 또는 총 라운드 수를 우선 표시하도록 정리했다.
- 위 정합성 수정 배포 버전은 `b2013cb0-b2de-478d-a860-20ba8ef377ab` 이다.
- 가입 흐름 실응답 점검 결과 `POST /api/auth/signup` 은 pending 가입만 만들고, 인증 전 `POST /api/auth/login` 은 `이메일 인증이 아직 완료되지 않았습니다` 로 차단된다.
- `/simulation/:simulationId` 진입 시 Step2 화면이 실행 중 시뮬레이션을 무조건 중지하던 경로를 수정했다. 이제 `SimulationRunView` 에서 명시적으로 `stopRunning=1` 쿼리로 돌아온 경우에만 정리하고, 단순 재진입/새로고침으로는 러닝 시뮬레이션을 끊지 않는다.
- 프로젝트 삭제 시 연관 `files`, `simulations`, 관련 `job_queue` 와 R2 업로드 파일이 남을 수 있는 경로를 `workers/src/projects.js` 에서 정리했다. 이제 프로젝트 삭제 시 보고서 외에도 프로젝트 파일/시뮬레이션/큐 자산까지 함께 정리한다.
- 위 사용자 플로우 정합성 수정 배포 버전은 `85aa64b4-a028-4c4e-a253-86dd3e33d7c6` 이다.
- 결제 후 프로젝트 생성 실패 복구 경로를 다시 점검했다. Worker 결제/프로젝트 경로는 `payment_orders.status='confirmed' AND project_id IS NULL` 인 주문을 기준으로 복구 가능 상태를 유지하고, 온톨로지/프로젝트 생성 실패 시 `releaseSimulationPayment()` 로 예약 결제를 다시 `confirmed` 로 되돌린다.
- 보고서 생성 중 브라우저 이탈/복귀 정합성을 보강했다. `frontend/src/components/Step4Report.vue` 는 탭/앱 복귀 시 `visibilitychange` 에서 즉시 agent log, console log, progress 를 재조회하고 필요하면 polling 을 재시작한다.
- 홈/히스토리 목록 즉시 반영을 보강했다. `frontend/src/views/Home.vue` 와 `frontend/src/views/History.vue` 는 `focus`, `visibilitychange`, 커스텀 이벤트 `tiresias:projects-changed` 에서 프로젝트 목록을 다시 조회한다.
- 히스토리에서 프로젝트 삭제 성공 시 `window.dispatchEvent(new CustomEvent('tiresias:projects-changed'))` 를 발생시켜 홈/히스토리의 최근 목록이 같은 세션에서 즉시 갱신되도록 했다.
- 위 정합성/복귀 보강 수정 배포 버전은 `440d0ca9-f1fc-47d5-aafc-9581f24a4010` 이다.
- 2026-03-24 사용자 제보 `결제는 완료됐는데 보고서가 비어 보였다` 건을 점검했다. 맥미니 백엔드 `uploads/reports` 기준 최신 완료 보고서는 2026-03-22 `report_9ee0637e4ca1` 이고, 오늘 새 보고서 폴더가 생성되지 않았다. 즉 이 케이스는 보고서 본문 생성 실패라기보다 결제 후 프로젝트/보고서 생성 흐름까지 도달하지 못한 가능성이 높다.
- `frontend/src/views/Credits.vue` 는 이제 Toss 결제 콜백을 받으면 결제 내역 페이지를 그리지 않고 즉시 결제 확인/리다이렉트 전용 로더만 표시한다. 시뮬레이션 결제 성공 시 `Process(new)` 로 바로 넘겨 보고서 생성 흐름을 이어간다.
- `frontend/src/views/Credits.vue` 는 결제 실패/취소 콜백도 처리 후 홈으로 되돌린다. 더 이상 결제 콜백 때문에 결제 내역 페이지에 머무르지 않는다.
- `frontend/src/views/Home.vue` 는 시뮬레이션 유료 결제 전에 업로드 대기 상태가 durable save(원격 또는 IndexedDB)되지 않았으면 Toss 결제를 시작하지 않게 막았다. 이로써 결제 완료 후 파일 복원이 안 되어 프로젝트/보고서가 시작되지 않는 경로를 줄였다.
- 위 결제 콜백/복구 보강 배포 버전은 `a4eedd7d-2452-4db3-a882-c46a7685c8a3` 이다.
- 2026-03-24 PDF 다운로드를 무료로 전환했다. `workers/src/index.js` 의 `/api/report/pdf/:reportId` 경로에서 PDF 결제 주문 확인과 `402 PDF_PAYMENT_REQUIRED` 응답을 제거했다.
- 프론트 `frontend/src/components/Step4Report.vue`, `frontend/src/views/History.vue`, `frontend/src/utils/pdfPayment.js` 도 PDF 다운로드 시 결제 모달/결제 시작 로직 없이 바로 다운로드만 시도하도록 정리했다.
- 과거 `pdf_payment` / `pdf_refund` 거래 이력은 그대로 남지만, 새 PDF 다운로드에는 더 이상 결제 흐름이 개입하지 않는다.
- 위 PDF 무료화 배포 버전은 `31b2ed7b-cd35-44eb-b88f-8a9c0c6cd5e8` 이다.
- 사용자 제보: 첫 결제 직후에는 보고서 생성이 안 되고, 다시 결제 시도로 들어가면 추가 결제 없이 그제서야 생성이 시작되는 경로가 있었다.
- 원인 후보는 `Credits` 결제 콜백 직후 `getPendingUpload()` 가 즉시 false를 반환하는 순간이 있고, 기존 구현은 그 전에 `pending_order` 를 지워서 자동 복귀를 끊어버리는 점이었다.
- `frontend/src/views/Credits.vue` 에 `resolvePendingUploadWithRetry()` 를 추가해 결제 직후 업로드 복원을 3회 재시도하게 했다.
- 시뮬레이션 결제 성공 후에는 pending upload 복원이 실제로 확인되기 전까지 `clearPendingOrder()` 를 하지 않도록 바꿨다. 복원이 실패해도 홈으로 돌아가면 같은 confirmed 주문을 추가 결제 없이 이어갈 수 있다.
- 위 결제 직후 자동 복귀 보강 배포 버전은 `31c90c23-c3a5-4496-9d97-3d395b7f4bbe` 이다.
- 홈 첫 화면에서 사용법이 추상적으로 보여 `무슨 파일을 넣고 어떤 문장으로 요청해야 하는지` 이해가 늦는 피드백이 있었다.
- `frontend/src/views/Home.vue` 입력 영역 상단에 `이런 식으로 요청하세요` 가이드를 추가했다. 정책 분석 / 시장 예측 / 스토리 전개 3개 예시 탭을 제공하고, 선택한 예시를 textarea에 바로 넣는 `예시 넣기` 버튼을 붙였다.
- topic textarea placeholder 도 선택된 예시 유형에 맞게 바뀌도록 연결했다.
- 위 홈 입력 가이드 개선 배포 버전은 `5c484903-0941-4bc5-ae95-02f169d885cf` 이다.
- 2026-03-27 관리자 직권 비밀번호 초기화 흐름을 추가했다. `workers/src/admin.js` 에 관리자 `POST /api/admin/users/:id/reset-password` 와 내부용 `POST /api/admin/internal/reset-password` 를 넣어 임시 비밀번호를 생성하고 Resend 로 메일 발송한다.
- 이때 `users.must_change_password` 플래그를 1로 올리고, 로그인 후에는 `frontend/src/router/index.js` 와 `frontend/src/main.js` 가 사용자를 `/profile?forcePassword=1` 로 강제 이동시킨다.
- `frontend/src/views/Profile.vue` 에 비밀번호 변경 카드와 `/api/auth/change-password` 연동을 추가했다. 사용자가 현재 임시 비밀번호와 새 비밀번호를 입력하면 `must_change_password` 를 0으로 내리고 새 세션 쿠키/JWT를 재발급한다.
- 초기화 메일 발송 실패 시 기존 `password_hash` 와 `must_change_password` 상태로 롤백되도록 했다.
- D1 마이그레이션 `0012_add_must_change_password.sql` 을 원격 적용했고, 관련 배포 버전은 `160d53a9-abe6-49bb-b23f-94c89a620c18` 이다.
- 계정 `obh5been@naver.com` 에 대해 내부용 초기화 엔드포인트를 호출해 임시 비밀번호 메일 발송까지 완료했다.
