"use client";

import { Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useUserId } from "@/contexts/user-id-context";
import { ApiError, addWatchlistItem, listWatchlist, removeWatchlistItem } from "@/lib/api";
import type { WatchlistItemRead } from "@/lib/api/types";

export default function WatchlistPage() {
  const { userId, ready } = useUserId();
  const [items, setItems] = useState<WatchlistItemRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [symbol, setSymbol] = useState("");
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await listWatchlist(userId);
      setItems(res.items);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load watchlist");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (ready && userId) void load();
  }, [ready, userId, load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (!userId || !symbol.trim()) return;
    setAdding(true);
    try {
      await addWatchlistItem(userId, { symbol: symbol.trim() });
      setSymbol("");
      toast.success("Added to watchlist");
      await load();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(err.message);
      } else {
        toast.error("Could not add symbol");
      }
    } finally {
      setAdding(false);
    }
  }

  async function remove(sym: string) {
    if (!userId) return;
    try {
      await removeWatchlistItem(userId, sym);
      toast.success(`Removed ${sym}`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Remove failed");
    }
  }

  return (
    <>
      <PageHeader
        title="Watchlist"
        description="Symbols you are tracking for AI-driven ideas and alerts."
      />

      <form onSubmit={add} className="mb-8 flex max-w-lg flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-2">
          <Label htmlFor="symbol">Symbol</Label>
          <Input
            id="symbol"
            placeholder="e.g. AAPL"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            autoCapitalize="characters"
          />
        </div>
        <Button type="submit" disabled={!ready || !userId || adding || !symbol.trim()}>
          Add
        </Button>
      </form>

      <div className="rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead className="hidden sm:table-cell">Notes</TableHead>
              <TableHead className="w-[100px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={3} className="text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-muted-foreground">
                  No symbols yet. Add one above.
                </TableCell>
              </TableRow>
            ) : (
              items.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium">{row.symbol}</TableCell>
                  <TableCell className="hidden max-w-md truncate text-muted-foreground sm:table-cell">
                    {row.notes ?? "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={`Remove ${row.symbol}`}
                      onClick={() => void remove(row.symbol)}
                    >
                      <Trash2 className="size-4 shrink-0 opacity-70" />
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
