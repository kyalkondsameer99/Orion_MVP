"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getBrokerAccount } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [cash, setCash] = useState<string | null>(null);
  const [equity, setEquity] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const acc = await getBrokerAccount();
        if (cancelled) return;
        setCash(acc.cash);
        setEquity(acc.equity);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 503) {
          setCash(null);
          setEquity(null);
        } else {
          toast.error(e instanceof Error ? e.message : "Could not load account");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Paper trading overview and quick access to your copilot tools."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <>
            <Skeleton className="h-28 rounded-xl" />
            <Skeleton className="h-28 rounded-xl" />
          </>
        ) : (
          <>
            <StatCard
              title="Cash"
              value={cash ?? "—"}
              hint={
                cash ? undefined : "Configure Alpaca keys on the API to load live paper data."
              }
            />
            <StatCard title="Equity" value={equity ?? "—"} />
          </>
        )}
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
            <CardDescription>Jump into the main workflows.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Link
              href="/watchlist"
              className={cn(buttonVariants({ variant: "secondary" }), "inline-flex")}
            >
              Manage watchlist
            </Link>
            <Link
              href="/recommendations"
              className={cn(buttonVariants({ variant: "secondary" }), "inline-flex")}
            >
              Run analysis
            </Link>
            <Link
              href="/orders"
              className={cn(buttonVariants({ variant: "secondary" }), "inline-flex")}
            >
              Order history
            </Link>
            <Link
              href="/positions"
              className={cn(buttonVariants({ variant: "outline" }), "inline-flex")}
            >
              View positions
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>API</CardTitle>
            <CardDescription>
              This UI talks to the FastAPI backend via{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">/api/backend</code>{" "}
              (Next rewrites to <code className="rounded bg-muted px-1 py-0.5 text-xs">/api/v1</code>
              ).
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Set <code className="text-xs">BACKEND_ORIGIN</code> if your API is not on{" "}
            <code className="text-xs">127.0.0.1:8000</code>.
          </CardContent>
        </Card>
      </div>
    </>
  );
}
