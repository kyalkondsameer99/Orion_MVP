import { Separator } from "@/components/ui/separator";
import type { RecommendationResponse } from "@/lib/api/types";

import { RecommendationActionBadge } from "@/components/recommendations/recommendation-action-badge";
import {
  formatConfidence,
  formatPrice,
  formatRewardRisk,
} from "@/components/recommendations/format";

function SummaryBlock({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </h3>
      <p className="text-sm leading-relaxed text-foreground">{body || "—"}</p>
    </div>
  );
}

function PriceCell({
  label,
  value,
  emphasize,
}: {
  label: string;
  value: string;
  emphasize?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border border-border/80 bg-muted/30 px-3 py-2.5 ${
        emphasize ? "ring-1 ring-primary/20" : ""
      }`}
    >
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-0.5 font-mono text-base font-semibold tabular-nums">{value}</p>
    </div>
  );
}

export type RecommendationDetailProps = {
  symbol: string;
  data: RecommendationResponse;
  /** When persisted, show workflow metadata */
  recordId?: string | null;
  recordStatus?: string | null;
};

export function RecommendationDetail({
  symbol,
  data,
  recordId,
  recordStatus,
}: RecommendationDetailProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Symbol
          </p>
          <p className="mt-1 text-3xl font-bold tracking-tight tabular-nums">{symbol}</p>
          {(recordId || recordStatus) && (
            <p className="mt-2 text-xs text-muted-foreground">
              {recordId && (
                <>
                  ID <span className="font-mono text-[11px]">{recordId}</span>
                </>
              )}
              {recordId && recordStatus ? " · " : null}
              {recordStatus ? <span className="capitalize">{recordStatus}</span> : null}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <RecommendationActionBadge action={data.action} />
          <span className="rounded-md border border-border bg-muted/50 px-2 py-1 text-xs text-muted-foreground">
            {data.direction}
          </span>
          <span
            className={`rounded-md border px-2 py-1 text-xs font-medium ${
              data.passed_risk_checks
                ? "border-emerald-600/30 bg-emerald-600/10 text-emerald-800 dark:text-emerald-200"
                : "border-amber-600/30 bg-amber-600/10 text-amber-900 dark:text-amber-100"
            }`}
          >
            Risk {data.passed_risk_checks ? "passed" : "check failed"}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-baseline gap-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Confidence
        </span>
        <span className="text-2xl font-semibold tabular-nums">
          {formatConfidence(data.confidence)}
        </span>
        {data.reward_risk_ratio != null && (
          <span className="text-sm text-muted-foreground">
            Reward:risk <span className="font-mono">{formatRewardRisk(data.reward_risk_ratio)}</span>
          </span>
        )}
      </div>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Levels
        </p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <PriceCell label="Entry" value={formatPrice(data.entry_price)} emphasize />
          <PriceCell label="Stop loss" value={formatPrice(data.stop_loss)} />
          <PriceCell label="Take profit" value={formatPrice(data.take_profit)} />
        </div>
      </div>

      <Separator />

      <div className="grid gap-6 md:grid-cols-1">
        <SummaryBlock title="Technical summary" body={data.technical_summary} />
        <SummaryBlock title="News summary" body={data.news_summary} />
        <SummaryBlock title="Reason summary" body={data.reason_summary} />
      </div>
    </div>
  );
}
