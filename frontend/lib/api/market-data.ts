import { apiFetch } from "@/lib/api/client";
import type { MarketAnalysisResponse, OHLCVResponse } from "@/lib/api/types";

export async function getOhlcv(
  symbol: string,
  params: {
    timeframe: "daily" | "intraday";
    interval: string;
    limit?: number;
  },
): Promise<OHLCVResponse> {
  const q = new URLSearchParams({
    timeframe: params.timeframe,
    interval: params.interval,
    limit: String(params.limit ?? 120),
  });
  return apiFetch<OHLCVResponse>(`/market-data/${encodeURIComponent(symbol)}/ohlcv?${q}`);
}

export async function getAnalysis(
  symbol: string,
  params: {
    timeframe: "daily" | "intraday";
    interval: string;
    limit?: number;
  },
): Promise<MarketAnalysisResponse> {
  const q = new URLSearchParams({
    timeframe: params.timeframe,
    interval: params.interval,
    limit: String(params.limit ?? 120),
  });
  return apiFetch<MarketAnalysisResponse>(
    `/market-data/${encodeURIComponent(symbol)}/analysis?${q}`,
  );
}
