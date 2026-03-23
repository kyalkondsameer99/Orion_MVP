# Architecture (MVP)

## Flow

```text
Next.js UI  --/api/backend/*-->  FastAPI (/api/v1/...)
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
   Watchlist                   Market data                 News + sentiment
   CRUD                        + indicators                (rules / yfinance)
        |                           |                           |
        +---------------------------+---------------------------+
                                    |
                         Recommendation engine (deterministic)
                                    |
                         Persist → approve/reject → submit (Alpaca paper)
                                    |
                         PostgreSQL (recommendations, orders, positions, audit)
                                    |
                         Redis + RQ workers (position monitor, enqueue jobs)
```

## Stack

| Layer | Technology |
|-------|------------|
| UI | Next.js 15, TypeScript, Tailwind, shadcn-style components |
| API | FastAPI, Pydantic v2, `/api/v1` prefix |
| ORM | SQLAlchemy 2, Alembic |
| DB | PostgreSQL |
| Jobs | Redis + **RQ** (Celery-compatible role) |
| Broker | Alpaca paper (`DELETE /v2/positions/{symbol}` for exit) |

## Safety

- **TRADING_ENABLED** — when `false`, persist/approve/submit, broker `POST /orders`, and position exit return **403**.  
- **MAX_OPEN_POSITIONS** — enforced on **submit to broker** using Alpaca open position count.  
- **Manual approval** — orders are not sent until the user approves and submits.

## Starter-pack route aliases

| Documented path | Implementation |
|-----------------|----------------|
| `POST /recommendations/generate` | `POST /api/v1/recommendations/generate` |
| `GET /positions` (broker) | `GET /api/v1/positions/` |
| `POST /orders/place` | `POST /api/v1/orders/place` `{ "recommendation_id": "..." }` |

All product routes live under **`/api/v1`**.
