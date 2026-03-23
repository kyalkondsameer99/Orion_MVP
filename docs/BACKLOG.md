# Orion MVP — prioritized backlog

Aligned with the end-to-end demo (watchlist → generate → approve → paper order → positions → PnL → exit suggestion) and the gaps vs the full Cursor build plan.

## P0 — Unblock the demo story

1. **`GET /api/v1/recommendations`** — List persisted recommendations for the current user (filters: status, symbol, limit). Enables refresh after navigation and a truthful “recent recommendations” surface without client-only state.
2. **Wire the recommendations UI** to load from that endpoint (and keep analyze/persist/approve/submit flows). Empty loading/error states already exist; ensure list survives reload.
3. ~~**`GET /api/v1/orders/`**~~ — **Done:** lists internal `TradeOrder` rows (`status`, `symbol`, `limit` query params). Alpaca remote history remains **`GET /api/v1/broker/orders`**.
4. ~~**Orders page (`/orders`)**~~ — **Done:** table + sidebar + dashboard link; shows `recommendation_id` (short) and timestamps.

## P1 — Positions & exits (plan §8 / §10)

5. ~~**`POST /api/v1/positions/exit`** + **`POST /api/v1/positions/{id}/exit`**~~ — **Done:** Alpaca `DELETE /v2/positions/{symbol}`, internal `positions` rows closed, audit `position.exit_broker`. UI: Close on `/positions`.
6. **Positions page enhancements** — Show SL/TP and exit-suggestion copy when backend exposes them (from DB/RQ monitor); optional “Close position” using (5).
7. **`GET /api/v1/positions/{symbol}`** — Optional detail view if you need per-symbol drill-down beyond the broker list.

## P2 — Product polish & safety

8. **Config flags** — `TRADING_ENABLED`, `MAX_RISK_PERCENT_PER_TRADE`, `MAX_OPEN_POSITIONS` (read in recommendation + workflow services; return 403 when disabled).
9. **Replace `X-User-Id` with real auth** — JWT or session; keep a dev header override for local testing.
10. **Broker secrets** — Either document env-only Alpaca for single-tenant MVP or implement `BrokerConnection` + encryption/KMS path for multi-user.

## P3 — Data & “AI” depth

11. **News provider** — Add Finnhub or NewsAPI adapter behind `NewsProvider` (keep yfinance/stub as fallbacks).
12. **LLM sentiment/summary** — Implement `score_headlines` (and optional catalyst summary) behind `SENTIMENT_ENGINE=llm` with `OPENAI_API_KEY` (or similar) in config.
13. **Charts** — Add Recharts (or embed TradingView) on dashboard or watchlist symbol detail for OHLCV.

## P4 — Quality

14. **Frontend tests** — Playwright or React Testing Library for watchlist + recommendation approve path (minimal smoke).
15. **Architecture docs** — Root `README` section or `docs/architecture.md`: API map vs the plan, env vars, and demo script checklist.

---

**Suggested order:** 1 → 2 → 3 → 4 → 5 → 6, then 8–9 as you harden for anyone other than yourself, then 11–13 by priority.
