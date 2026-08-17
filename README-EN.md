# Tiresias View

## Overview

Tiresias View is a document-driven simulation service for policy, market, and public-opinion analysis.

- Users upload PDF, Markdown, or TXT documents.
- The system builds an ontology and knowledge graph from the source material.
- Personas and simulation environments are prepared from that graph.
- Simulation results are turned into reports and downloadable PDFs.
- Completed reports can be revisited and downloaded from history.

## Current Architecture

- `frontend/`: Vue 3 + Vite client
- `workers/`: Cloudflare Worker, D1, R2, auth, payments, queueing
- `backend/`: Flask API for graph build, simulation, and report generation

Current production topology:

- Frontend and Worker are deployed from this repository.
- The Worker is the public `/api/*` entrypoint.
- The Worker currently proxies heavy backend traffic to `https://api.tiresiasview.com`.
- The underlying backend host machine or server path is not fixed in this repo.
- Neo4j is the configured graph backend.
- OpenAI-compatible APIs are the active LLM path.
- Report PDFs are rendered by the backend through Node + Playwright.

## Local Development

```bash
cp .env.example .env
npm run setup:all
npm run dev
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5001`

Run services separately:

```bash
npm run frontend
npm run backend
```

## Deployment

Frontend + Worker:

```bash
npm run deploy
```

Remote D1 migrations:

```bash
cd workers
npx wrangler d1 migrations apply tiresias-db --remote
```

Backend deployment and restart are managed outside this repository.
Do not treat this README as a source of truth for a specific host machine.

## Operational Notes

- Toss Payments is used for checkout flows.
- Report PDFs are rendered through the shared backend renderer and cached in R2.
- Heavy jobs are processed through a Worker-side queue.
- Technical identifiers now use the `tiresias` slug.
- The Worker proxies `/api/graph`, `/api/simulation`, and `/api/report` routes to the backend with the internal key.

## Additional Docs

- Korean guide: [README-KO.md](./README-KO.md)
- Google Ads playbook: [docs/marketing/google-ads-playbook.md](./docs/marketing/google-ads-playbook.md)
- Attribution and change notice: [NOTICE.md](./NOTICE.md)
