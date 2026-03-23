import { Button } from "@/components/ui/button";

export type RecommendationApprovalActionsProps = {
  onApprove: () => void | Promise<void>;
  onReject: () => void | Promise<void>;
  disabled?: boolean;
  loading?: boolean;
  /** When false, buttons are hidden or disabled (e.g. not persisted yet) */
  canAct?: boolean;
};

export function RecommendationApprovalActions({
  onApprove,
  onReject,
  disabled,
  loading,
  canAct = true,
}: RecommendationApprovalActionsProps) {
  const busy = Boolean(loading || disabled);

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
      <Button
        type="button"
        variant="default"
        className="min-w-[120px]"
        disabled={!canAct || busy}
        onClick={() => void onApprove()}
      >
        {loading ? "Working…" : "Approve"}
      </Button>
      <Button
        type="button"
        variant="outline"
        className="min-w-[120px]"
        disabled={!canAct || busy}
        onClick={() => void onReject()}
      >
        {loading ? "Working…" : "Reject"}
      </Button>
    </div>
  );
}
