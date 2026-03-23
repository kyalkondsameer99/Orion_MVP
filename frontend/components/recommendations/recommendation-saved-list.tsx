"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { RecommendationRecordOut } from "@/lib/api/types";

function formatWhen(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export type RecommendationSavedListProps = {
  items: RecommendationRecordOut[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
  onSelect: (row: RecommendationRecordOut) => void;
  onRetry: () => void;
};

export function RecommendationSavedList({
  items,
  loading,
  error,
  selectedId,
  onSelect,
  onRetry,
}: RecommendationSavedListProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Saved recommendations</CardTitle>
        <CardDescription>
          Loaded from <code className="text-xs">GET /recommendations/</code>. Select a row to
          continue approval or submit.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            <p>{error}</p>
            <Button type="button" variant="outline" size="sm" className="mt-2" onClick={onRetry}>
              Retry
            </Button>
          </div>
        )}

        {loading && !error && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No saved recommendations yet. Run analysis and choose &quot;Save as pending&quot;.
          </p>
        )}

        {!loading && !error && items.length > 0 && (
          <ScrollArea className="h-[min(420px,50vh)] rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden sm:table-cell">Action</TableHead>
                  <TableHead className="hidden md:table-cell">Updated</TableHead>
                  <TableHead className="text-right">Open</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => {
                  const active = selectedId === row.id;
                  return (
                    <TableRow
                      key={row.id}
                      className={active ? "bg-muted/50" : undefined}
                      data-state={active ? "selected" : undefined}
                    >
                      <TableCell className="font-medium">{row.symbol}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="capitalize">
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground sm:table-cell">
                        {row.recommendation_action ?? "—"}
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground md:table-cell">
                        {formatWhen(row.updated_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          type="button"
                          variant={active ? "secondary" : "outline"}
                          size="sm"
                          onClick={() => onSelect(row)}
                        >
                          {active ? "Selected" : "Open"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
