# Starter pack vs Orion MVP

See **`docs/architecture.md`** for the current API map.

## Resolved for MVP run

- `docs/architecture.md`, `infra/README.md`
- Env: `SECRET_KEY`, `APP_ENV` → `ENVIRONMENT`, `ALPACA_API_KEY` / `ALPACA_API_SECRET` aliases, `TRADING_ENABLED`, `MAX_OPEN_POSITIONS`, optional `NEWS_API_KEY` / `OPENAI_API_KEY` in settings
- API aliases: `POST /api/v1/recommendations/generate`, `GET /api/v1/positions/`, `POST /api/v1/orders/place`
- Kill switch + max open positions enforcement

## Optional follow-ups

- Wire **NewsAPI/Finnhub** and **OpenAI** adapters
- **JWT** auth instead of `X-User-Id`
- **Charts** (Recharts / TradingView)
- **Frontend** tests
