import { apiFetch } from "@/lib/api/client";
import type { TradeOrderListResponse } from "@/lib/api/types";

export type ListInternalOrdersParams = {
  status?: string;
  symbol?: string;
  limit?: number;
};

/** DB-backed internal orders (approval workflow). For Alpaca remote history use broker API. */
export async function listInternalOrders(
  userId: string,
  params?: ListInternalOrdersParams,
): Promise<TradeOrderListResponse> {
  const sp = new URLSearchParams();
  if (params?.status) sp.set("status", params.status);
  if (params?.symbol) sp.set("symbol", params.symbol);
  if (params?.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  const path = q ? `/orders/?${q}` : "/orders/";
  return apiFetch<TradeOrderListResponse>(path, { method: "GET", userId });
}
