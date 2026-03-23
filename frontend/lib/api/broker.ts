import { apiFetch } from "@/lib/api/client";
import type { AccountOut, PositionExitResponse, PositionListOut } from "@/lib/api/types";

/** Alpaca-backed; no X-User-Id on broker routes in current API. */
export async function getBrokerAccount(): Promise<AccountOut> {
  return apiFetch<AccountOut>("/broker/account");
}

export async function getBrokerPositions(): Promise<PositionListOut> {
  return apiFetch<PositionListOut>("/broker/positions");
}

/** Same data as `getBrokerPositions` — `GET /api/v1/positions/` (starter-pack path). */
export async function getOpenPositions(): Promise<PositionListOut> {
  return apiFetch<PositionListOut>("/positions/");
}

/** Close entire symbol at Alpaca + reconcile internal `positions` rows (requires `X-User-Id`). */
export async function exitPaperPosition(
  userId: string,
  symbol: string,
): Promise<PositionExitResponse> {
  return apiFetch<PositionExitResponse>("/positions/exit", {
    method: "POST",
    body: JSON.stringify({ symbol: symbol.trim().toUpperCase() }),
    userId,
  });
}
