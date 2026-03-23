/** Mirrors backend Pydantic models (JSON shapes). */

export type WatchlistItemRead = {
  id: string;
  user_id: string;
  symbol: string;
  sort_order: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type WatchlistListResponse = {
  items: WatchlistItemRead[];
};

export type WatchlistItemCreate = {
  symbol: string;
  sort_order?: number;
  notes?: string | null;
};

export type CandleOut = {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type OHLCVResponse = {
  symbol: string;
  timeframe: "daily" | "intraday";
  interval: string;
  candles: CandleOut[];
};

export type SeriesFloat = {
  window: number;
  values: (number | null)[];
};

export type MarketAnalysisResponse = OHLCVResponse & {
  rsi: SeriesFloat;
  sma: SeriesFloat;
  ema: SeriesFloat;
  macd: {
    fast: number;
    slow: number;
    signal: number;
    line: (number | null)[];
    signal_line: (number | null)[];
    histogram: (number | null)[];
  };
  atr: SeriesFloat;
  volume_zscore: SeriesFloat;
  volume_spike: (boolean | null)[];
};

export type NewsContextIn = {
  sentiment: "positive" | "neutral" | "negative";
  sentiment_score: number;
  summary?: string;
};

export type TechnicalIndicatorsIn = {
  rsi?: number | null;
  ema?: number | null;
  sma?: number | null;
  macd_line?: number | null;
  macd_signal?: number | null;
  macd_histogram?: number | null;
  atr?: number | null;
};

export type RecommendationRequest = {
  symbol: string;
  candles: CandleOut[];
  indicators: TechnicalIndicatorsIn;
  news: NewsContextIn;
  account_size: string;
  risk_percent: number;
};

export type RecommendationResponse = {
  action: "BUY" | "SELL" | "HOLD";
  direction: "LONG" | "SHORT" | "NONE";
  entry_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  confidence: number;
  technical_summary: string;
  news_summary: string;
  reason_summary: string;
  passed_risk_checks: boolean;
  reward_risk_ratio: number | null;
};

export type PersistRecommendationRequest = {
  symbol: string;
  engine: RecommendationResponse;
  account_size: string;
  risk_percent: number;
  quantity?: string | null;
};

export type RecommendationRecordOut = {
  id: string;
  user_id: string;
  symbol: string;
  status: string;
  recommendation_action: string | null;
  trade_direction: string | null;
  entry_price: string | null;
  stop_loss: string | null;
  take_profit: string | null;
  quantity: string | null;
  trade_order_id: string | null;
  created_at: string;
  updated_at: string;
  confidence?: number | null;
  technical_summary?: string | null;
  news_summary?: string | null;
  reason_summary?: string | null;
  passed_risk_checks?: boolean | null;
  reward_risk_ratio?: number | null;
};

export type RecommendationActionResult = {
  recommendation: RecommendationRecordOut;
  trade_order_id?: string | null;
  message?: string;
};

export type RecommendationListResponse = {
  items: RecommendationRecordOut[];
};

export type RecommendationSubmitResult = {
  recommendation_id: string;
  broker_order_id: string | null;
  message?: string;
};

export type AccountOut = {
  id: string;
  cash: string;
  equity: string;
  buying_power: string | null;
  currency?: string;
};

export type PositionOut = {
  symbol: string;
  qty: string;
  side: "long" | "short";
  avg_entry_price: string;
  market_value: string | null;
  cost_basis: string | null;
  unrealized_pl: string | null;
  asset_class?: string | null;
};

export type PositionListOut = {
  positions: PositionOut[];
};

/** Mirrors `TradeOrderRead` — internal DB row (not Alpaca remote order). */
export type TradeOrderRead = {
  id: string;
  user_id: string;
  broker_connection_id: string | null;
  recommendation_id: string | null;
  client_order_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: string;
  limit_price: string | null;
  stop_price: string | null;
  time_in_force: string | null;
  paper_trade: boolean;
  status: string;
  filled_quantity: string;
  avg_fill_price: string | null;
  submitted_at: string | null;
  filled_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TradeOrderListResponse = {
  items: TradeOrderRead[];
};

/** Broker order returned when closing a position (Alpaca DELETE position). */
export type BrokerOrderOut = {
  id: string;
  client_order_id: string | null;
  symbol: string;
  side: string;
  order_type: string;
  qty: string;
  filled_qty: string;
  status: string;
  submitted_at: string | null;
  filled_avg_price: string | null;
  limit_price: string | null;
  raw?: unknown;
};

export type PositionExitResponse = {
  broker_order: BrokerOrderOut;
  closed_internal_positions: number;
  message: string;
};
