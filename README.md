# Orion MVP (AI Paper Trading Copilot)

Full-stack **paper trading** MVP: deterministic signals + news context, **manual approval**, **Alpaca paper** execution, position monitoring, and audit logs.

**Docs:** [Architecture](docs/architecture.md) · [Starter-pack gap checklist](docs/STARTER_PACK_GAP_CHECKLIST.md)

## MVP checklist (what this repo delivers)

- [x] Watchlist, market data + indicators, news/sentiment (rules + pluggable providers)  
- [x] Recommendation engine → persist → approve / reject → submit to Alpaca  
- [x] Internal **orders** list + broker account / positions / orders  
- [x] **Kill switch:** `TRADING_ENABLED` (blocks trades when `false`)  
- [x] **Max open positions** at broker on submit (`MAX_OPEN_POSITIONS`)  
- [x] Position **exit** (Alpaca close) + optional internal `positions` rows  
- [x] RQ workers (optional Compose profile) for position monitoring  
- [x] Starter-pack **API aliases:** `POST /api/v1/recommendations/generate`, `GET /api/v1/positions/`, `POST /api/v1/orders/place`  

**Auth:** header `X-User-Id` (UUID) for user-scoped routes — swap for JWT when you harden.

## Quick start with Docker Compose

1. **Optional: copy environment file**

   Compose runs with sensible defaults. To customize ports, passwords, or Alpaca keys:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`, then start with:

   ```bash
   docker compose --env-file .env up --build
   ```

2. **Start the stack** (Postgres, Redis, backend API, frontend)

   ```bash
   docker compose up --build
   ```

3. **Open the app**

   - Frontend: [http://localhost:3000](http://localhost:3000) (or `FRONTEND_PORT` from `.env`)
   - Backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs) (or `BACKEND_PORT`)

The frontend calls the API through Next.js rewrites: browser requests go to `/api/backend/*`, and the Next server proxies them to the backend service (`BACKEND_ORIGIN=http://backend:8000` at build time in Docker).

### How services are wired

| Service    | Role |
|-----------|------|
| `postgres` | Database; healthcheck before dependents start |
| `redis`    | Redis for optional RQ workers |
| `backend`  | FastAPI on port 8000; waits for Postgres (script + `depends_on`), runs **Alembic** migrations on start |
| `frontend` | Next.js standalone on port 3000; proxies API traffic to `backend` |

### Backend startup

The backend image runs `scripts/wait_for_postgres.py`, then `alembic upgrade head`, then **Uvicorn**. To skip migrations (e.g. debugging), set `SKIP_DB_MIGRATIONS=1` on the service.

### Optional background workers

RQ workers are **not** started by default. To run them:

```bash
docker compose --profile workers up -d
```

This starts `rq-worker` and `position-monitor-scheduler` with `SKIP_DB_MIGRATIONS=1` so only the main API runs migrations.

### Environment variables

- Compose interpolates variables from your shell and from a file passed with **`docker compose --env-file .env up`**. If you do not use `--env-file`, built-in defaults (e.g. `orion` / `orion`) apply.
- `docker-compose.yml` sets **`DATABASE_URL`**, **`POSTGRES_HOST`**, and **`REDIS_URL`** inside containers to Docker network hostnames (`postgres`, `redis`, `backend`).
- For **local** backend/DB without Compose, use **`DATABASE_URL`** / **`POSTGRES_HOST=localhost`** in `.env` (see `.env.example`).

The API loads **`.env` from the repository root and from `backend/.env`** (if present), so you can keep a single root `.env` when running `uvicorn` from `backend/` — duplicate keys in `backend/.env` override the root file.

### Local development without Docker for all services

- Run Postgres and Redis via Compose only: `docker compose up postgres redis -d`
- Run backend: `cd backend && uvicorn app.main:app --reload` (set `POSTGRES_HOST=localhost` or `DATABASE_URL` in root or `backend/.env`)
- Run frontend: `cd frontend && npm run dev` (set `BACKEND_ORIGIN=http://127.0.0.1:8000` for API rewrites; optional `frontend/.env.local` from `frontend/.env.example`)

### Rebuilding the frontend after API URL changes

Docker bakes `BACKEND_ORIGIN` into the Next **build** for rewrites. If you change how the frontend reaches the API in Docker, rebuild:

```bash
docker compose build frontend --no-cache && docker compose up -d frontend
```

## Repository layout

- `backend/` — FastAPI app, Alembic, RQ tasks  
- `frontend/` — Next.js (App Router) UI  
- `docs/` — architecture notes, backlog, checklists  
- `infra/` — placeholder for future Terraform/cloud (local MVP uses Compose only)  
- `docker-compose.yml` — orchestration  
