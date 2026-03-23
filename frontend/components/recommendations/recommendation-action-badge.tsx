import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RecommendationResponse } from "@/lib/api/types";

type Action = RecommendationResponse["action"];

const styles: Record<Action, string> = {
  BUY: "bg-emerald-600/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border-emerald-600/20",
  SELL: "bg-rose-600/15 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300 border-rose-600/20",
  HOLD: "bg-amber-600/10 text-amber-800 dark:bg-amber-500/15 dark:text-amber-200 border-amber-600/15",
};

export function RecommendationActionBadge({
  action,
  className,
}: {
  action: Action;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-semibold uppercase tracking-wide", styles[action], className)}
    >
      {action}
    </Badge>
  );
}
