"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useUserId } from "@/contexts/user-id-context";
import { ApiError, listInternalOrders } from "@/lib/api";
import type { TradeOrderRead } from "@/lib/api/types";

function formatWhen(iso: string | null) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function OrdersPage() {
  const { userId, ready } = useUserId();
  const [rows, setRows] = useState<TradeOrderRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listInternalOrders(userId, { limit: 100 });
      setRows(res.items);
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Failed to load orders";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (!ready || !userId) {
      setLoading(false);
      return;
    }
    void load();
  }, [ready, userId, load]);

  return (
    <>
      <PageHeader
        title="Orders"
        description="Internal order records from the approval workflow (database). Alpaca remote history lives under the broker API."
      />

      {error && (
        <div className="mb-4 rounded-lg border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          <p>{error}</p>
          <Button type="button" variant="outline" size="sm" className="mt-2" onClick={() => void load()}>
            Retry
          </Button>
        </div>
      )}

      <div className="rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Side</TableHead>
              <TableHead className="text-right">Qty</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden lg:table-cell">Recommendation</TableHead>
              <TableHead className="hidden md:table-cell">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7}>
                  <div className="space-y-2 py-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                </TableCell>
              </TableRow>
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-muted-foreground">
                  {ready && userId
                    ? "No internal orders yet — save and approve a recommendation first."
                    : "Set a user id in the shell to load orders."}
                </TableCell>
              </TableRow>
            ) : (
              rows.map((o) => (
                <TableRow key={o.id}>
                  <TableCell className="font-medium">{o.symbol}</TableCell>
                  <TableCell>
                    <Badge variant={o.side === "buy" ? "default" : "secondary"}>{o.side}</Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{o.quantity}</TableCell>
                  <TableCell className="text-muted-foreground">{o.order_type}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {o.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden font-mono text-xs lg:table-cell">
                    {o.recommendation_id ? (
                      <span title={o.recommendation_id}>{o.recommendation_id.slice(0, 8)}…</span>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">
                    {formatWhen(o.created_at)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </>
  );
}
