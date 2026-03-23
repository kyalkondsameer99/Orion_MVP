import { AlertCircle, BarChart3, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function RecommendationLoadingState() {
  return (
    <Card className="overflow-hidden border-dashed">
      <CardContent className="space-y-6 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:justify-between">
          <div className="space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-9 w-32" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-7 w-16 rounded-full" />
            <Skeleton className="h-7 w-14 rounded-full" />
          </div>
        </div>
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <Skeleton className="h-20 rounded-lg" />
          <Skeleton className="h-20 rounded-lg" />
          <Skeleton className="h-20 rounded-lg" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/6" />
        </div>
      </CardContent>
    </Card>
  );
}

export function RecommendationErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <Alert variant="destructive" className="border-destructive/40">
      <AlertCircle className="size-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="text-destructive/90">
        {message}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 block text-sm font-medium underline underline-offset-4 hover:no-underline"
          >
            Try again
          </button>
        )}
      </AlertDescription>
    </Alert>
  );
}

export function RecommendationEmptyState({
  onRunSample,
  disabled,
}: {
  onRunSample?: () => void;
  disabled?: boolean;
}) {
  return (
    <Card className="border-dashed bg-muted/20">
      <CardContent className="flex flex-col items-center justify-center gap-4 py-14 text-center">
        <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
          <BarChart3 className="size-7" />
        </div>
        <div className="max-w-sm space-y-1">
          <h2 className="text-lg font-semibold tracking-tight">No recommendation yet</h2>
          <p className="text-sm text-muted-foreground">
            Set parameters on the left and run analysis to see AI-generated entry, stops, and
            summaries.
          </p>
        </div>
        {onRunSample && (
          <button
            type="button"
            disabled={disabled}
            onClick={onRunSample}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-muted disabled:pointer-events-none disabled:opacity-50"
          >
            <Sparkles className="size-4" />
            Run analysis
          </button>
        )}
      </CardContent>
    </Card>
  );
}
