"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useUserId } from "@/contexts/user-id-context";
import { ApiError, exitPaperPosition, getOpenPositions } from "@/lib/api";
import type { PositionOut } from "@/lib/api/types";

export default function PositionsPage() {
  const { userId, ready } = useUserId();
  const [rows, setRows] = useState<PositionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [closingSymbol, setClosingSymbol] = useState<string | null>(null);

  const loadPositions = useCallback(async () => {
    try {
      const res = await getOpenPositions();
      setRows(res.positions);
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        setRows([]);
        toast.message("Broker not configured", {
          description: "Set Alpaca keys on the API to load live paper positions.",
        });
      } else {
        toast.error(e instanceof Error ? e.message : "Failed to load positions");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPositions();
  }, [loadPositions]);

  async function handleClose(symbol: string) {
    if (!userId) {
      toast.error("Set a user id in the header to close positions.");
      return;
    }
    if (
      !window.confirm(
        `Submit a market order to fully close ${symbol} at Alpaca (paper)?`,
      )
    ) {
      return;
    }
    setClosingSymbol(symbol);
    try {
      const res = await exitPaperPosition(userId, symbol);
      toast.success(res.message || "Close submitted");
      await loadPositions();
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Close failed";
      toast.error(msg);
    } finally {
      setClosingSymbol(null);
    }
  }

  return (
    <>
      <PageHeader
        title="Positions"
        description="Open broker positions (Alpaca paper). Close submits DELETE /v2/positions/{symbol} via the API and updates internal rows when present."
      />

      <div className="rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Side</TableHead>
              <TableHead className="text-right">Qty</TableHead>
              <TableHead className="hidden text-right md:table-cell">Avg entry</TableHead>
              <TableHead className="hidden text-right lg:table-cell">Market value</TableHead>
              <TableHead className="text-right">Unrealized P&amp;L</TableHead>
              <TableHead className="w-[120px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-muted-foreground">
                  No open positions or broker unavailable.
                </TableCell>
              </TableRow>
            ) : (
              rows.map((p) => (
                <TableRow key={`${p.symbol}-${p.side}`}>
                  <TableCell className="font-medium">{p.symbol}</TableCell>
                  <TableCell>
                    <Badge variant={p.side === "long" ? "default" : "secondary"}>
                      {p.side}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{p.qty}</TableCell>
                  <TableCell className="hidden text-right tabular-nums md:table-cell">
                    {p.avg_entry_price}
                  </TableCell>
                  <TableCell className="hidden text-right tabular-nums lg:table-cell">
                    {p.market_value ?? "—"}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {p.unrealized_pl ?? "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={!ready || !userId || closingSymbol !== null}
                      title={
                        !userId
                          ? "Set User ID in the header (X-User-Id) to record the close."
                          : undefined
                      }
                      onClick={() => void handleClose(p.symbol)}
                    >
                      {closingSymbol === p.symbol ? "Closing…" : "Close"}
                    </Button>
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
