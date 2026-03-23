import type {
  MarketAnalysisResponse,
  OHLCVResponse,
  RecommendationRequest,
  TechnicalIndicatorsIn,
} from "@/lib/api/types";

function lastDefined<T>(values: (T | null | undefined)[]): T | undefined {
  for (let i = values.length - 1; i >= 0; i--) {
    const v = values[i];
    if (v !== null && v !== undefined) return v;
  }
  return undefined;
}

/**
 * Aligns OHLCV + analysis into the shape expected by `POST /recommendations/analyze`.
 */
export function buildRecommendationRequest(
  ohlcv: OHLCVResponse,
  analysis: MarketAnalysisResponse,
  accountSize: string,
  riskPercent: number,
): RecommendationRequest {
  const n = ohlcv.candles.length;
  const last = Math.max(0, n - 1);

  const macdLine = lastDefined(analysis.macd.line);
  const macdSig = lastDefined(analysis.macd.signal_line);
  const macdHist = lastDefined(analysis.macd.histogram);

  const indicators: TechnicalIndicatorsIn = {
    rsi: analysis.rsi.values[last] ?? lastDefined(analysis.rsi.values) ?? null,
    sma: analysis.sma.values[last] ?? lastDefined(analysis.sma.values) ?? null,
    ema: analysis.ema.values[last] ?? lastDefined(analysis.ema.values) ?? null,
    macd_line: macdLine ?? null,
    macd_signal: macdSig ?? null,
    macd_histogram: macdHist ?? null,
    atr: analysis.atr.values[last] ?? lastDefined(analysis.atr.values) ?? null,
  };

  return {
    symbol: ohlcv.symbol,
    candles: ohlcv.candles,
    indicators,
    news: {
      sentiment: "neutral",
      sentiment_score: 0,
      summary: "",
    },
    account_size: accountSize,
    risk_percent: riskPercent,
  };
}
