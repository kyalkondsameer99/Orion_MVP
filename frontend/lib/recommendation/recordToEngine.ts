import type { RecommendationRecordOut, RecommendationResponse } from "@/lib/api/types";

function parseDecimal(s: string | null | undefined): number | null {
  if (s == null || s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

/**
 * Build engine-shaped output from a persisted API row so `RecommendationDetail` can render.
 */
export function recordToRecommendationResponse(
  r: RecommendationRecordOut,
): RecommendationResponse | null {
  const action = (r.recommendation_action || "HOLD").toUpperCase();
  if (action !== "BUY" && action !== "SELL" && action !== "HOLD") {
    return null;
  }
  const direction = (r.trade_direction || "NONE").toUpperCase();
  const dir =
    direction === "LONG" || direction === "SHORT" || direction === "NONE"
      ? direction
      : "NONE";

  const entry = parseDecimal(r.entry_price);
  const stop = parseDecimal(r.stop_loss);
  const tp = parseDecimal(r.take_profit);

  return {
    action,
    direction: dir as RecommendationResponse["direction"],
    entry_price: entry,
    stop_loss: stop,
    take_profit: tp,
    confidence:
      r.confidence != null && Number.isFinite(Number(r.confidence))
        ? Math.min(1, Math.max(0, Number(r.confidence)))
        : 0,
    technical_summary: r.technical_summary ?? "—",
    news_summary: r.news_summary ?? "—",
    reason_summary: r.reason_summary ?? "—",
    passed_risk_checks: r.passed_risk_checks ?? true,
    reward_risk_ratio:
      r.reward_risk_ratio != null && Number.isFinite(Number(r.reward_risk_ratio))
        ? Number(r.reward_risk_ratio)
        : null,
  };
}
