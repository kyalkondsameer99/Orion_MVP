"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  RecommendationApprovalActions,
  RecommendationDetail,
  RecommendationEmptyState,
  RecommendationErrorState,
  RecommendationLoadingState,
  RecommendationSavedList,
} from "@/components/recommendations";
import { useUserId } from "@/contexts/user-id-context";
import {
  analyzeRecommendation,
  ApiError,
  approveRecommendation,
  getAnalysis,
  getOhlcv,
  listRecommendations,
  persistRecommendation,
  rejectRecommendation,
  submitRecommendation,
} from "@/lib/api";
import type { RecommendationRecordOut, RecommendationResponse } from "@/lib/api/types";
import { buildRecommendationRequest } from "@/lib/recommendation/buildAnalyzeRequest";
import { recordToRecommendationResponse } from "@/lib/recommendation/recordToEngine";

type WorkflowAction = "idle" | "analyze" | "persist" | "approve" | "reject" | "submit";

export default function RecommendationsPage() {
  const { userId, ready } = useUserId();
  const [symbol, setSymbol] = useState("AAPL");
  const [accountSize, setAccountSize] = useState("100000");
  const [riskPercent, setRiskPercent] = useState("1");

  const [engine, setEngine] = useState<RecommendationResponse | null>(null);
  const [recId, setRecId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const [savedItems, setSavedItems] = useState<RecommendationRecordOut[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);

  const [action, setAction] = useState<WorkflowAction>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isAnalyzing = action === "analyze";
  const workflowBusy = action !== "idle" && action !== "analyze";

  const refreshSavedList = useCallback(async () => {
    if (!userId) return;
    setListLoading(true);
    setListError(null);
    try {
      const res = await listRecommendations(userId, { limit: 50 });
      setSavedItems(res.items);
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Failed to load list";
      setListError(msg);
    } finally {
      setListLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (!ready || !userId) return;
    void refreshSavedList();
  }, [ready, userId, refreshSavedList]);

  useEffect(() => {
    if (!recId) return;
    const row = savedItems.find((x) => x.id === recId);
    if (row) setStatus(row.status);
  }, [savedItems, recId]);

  function applySavedRow(row: RecommendationRecordOut) {
    const eng = recordToRecommendationResponse(row);
    if (!eng) {
      toast.error("Could not load that recommendation for display.");
      return;
    }
    setSymbol(row.symbol);
    setRecId(row.id);
    setStatus(row.status);
    setEngine(eng);
    setErrorMessage(null);
  }

  async function runAnalyze() {
    setAction("analyze");
    setErrorMessage(null);
    setEngine(null);
    setRecId(null);
    setStatus(null);
    try {
      const sym = symbol.trim().toUpperCase();
      const [ohlcv, analysis] = await Promise.all([
        getOhlcv(sym, { timeframe: "intraday", interval: "1h", limit: 120 }),
        getAnalysis(sym, { timeframe: "intraday", interval: "1h", limit: 120 }),
      ]);
      const body = buildRecommendationRequest(
        ohlcv,
        analysis,
        accountSize,
        Number(riskPercent),
      );
      const out = await analyzeRecommendation(body);
      setEngine(out);
      toast.success("Analysis complete");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Analysis failed";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setAction("idle");
    }
  }

  async function runPersist() {
    if (!userId || !engine) return;
    setAction("persist");
    setErrorMessage(null);
    try {
      const res = await persistRecommendation(userId, {
        symbol: symbol.trim().toUpperCase(),
        engine,
        account_size: accountSize,
        risk_percent: Number(riskPercent),
      });
      setRecId(res.recommendation.id);
      setStatus(res.recommendation.status);
      toast.success(res.message || "Saved as pending");
      await refreshSavedList();
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Persist failed";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setAction("idle");
    }
  }

  async function runApprove() {
    if (!userId || !recId) return;
    setAction("approve");
    setErrorMessage(null);
    try {
      const res = await approveRecommendation(userId, recId);
      setStatus(res.recommendation.status);
      toast.success(res.message || "Approved");
      await refreshSavedList();
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Approve failed";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setAction("idle");
    }
  }

  async function runReject() {
    if (!userId || !recId) return;
    setAction("reject");
    setErrorMessage(null);
    try {
      const res = await rejectRecommendation(userId, recId);
      setStatus(res.recommendation.status);
      toast.success(res.message || "Rejected");
      await refreshSavedList();
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Reject failed";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setAction("idle");
    }
  }

  async function runSubmit() {
    if (!userId || !recId) return;
    setAction("submit");
    setErrorMessage(null);
    try {
      const res = await submitRecommendation(userId, recId);
      toast.success(res.message || "Submitted");
      await refreshSavedList();
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Submit failed";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setAction("idle");
    }
  }

  const canPersist = Boolean(ready && userId && engine);
  const canApproveReject = Boolean(ready && userId && recId && status === "pending");
  const approvalLoading = action === "approve" || action === "reject";

  const showDetail = Boolean(engine) && !isAnalyzing;
  const showEmpty =
    !engine && !isAnalyzing && !errorMessage && savedItems.length === 0 && !listLoading;
  const showPickHint =
    !engine && !isAnalyzing && !errorMessage && savedItems.length > 0 && !listLoading;
  const showError = Boolean(errorMessage) && !isAnalyzing;

  return (
    <>
      <PageHeader
        title="Recommendations"
        description="Run the engine, review levels and summaries, then persist and approve or reject."
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,340px)_1fr]">
        <div className="flex flex-col gap-6">
          <Card className="h-fit lg:sticky lg:top-20">
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
              <CardDescription>
                Intraday 1h OHLCV + indicators feed{" "}
                <code className="text-xs">POST /recommendations/analyze</code>.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="sym">Symbol</Label>
                <Input
                  id="sym"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  disabled={isAnalyzing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="acct">Account size</Label>
                <Input
                  id="acct"
                  inputMode="decimal"
                  value={accountSize}
                  onChange={(e) => setAccountSize(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="risk">Risk %</Label>
                <Input
                  id="risk"
                  inputMode="decimal"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>
              <Button
                className="w-full"
                onClick={() => void runAnalyze()}
                disabled={isAnalyzing || !symbol.trim() || workflowBusy}
              >
                {isAnalyzing ? "Analyzing…" : "Run analysis"}
              </Button>
            </CardContent>
          </Card>

          {ready && userId && (
            <RecommendationSavedList
              items={savedItems}
              loading={listLoading}
              error={listError}
              selectedId={recId}
              onSelect={applySavedRow}
              onRetry={() => void refreshSavedList()}
            />
          )}
        </div>

        <div className="flex min-h-[420px] flex-col gap-4">
          {showError && (
            <RecommendationErrorState
              message={errorMessage!}
              onRetry={
                engine
                  ? undefined
                  : () => {
                      setErrorMessage(null);
                      void runAnalyze();
                    }
              }
            />
          )}

          {isAnalyzing && <RecommendationLoadingState />}

          {showEmpty && (
            <RecommendationEmptyState
              disabled={isAnalyzing || workflowBusy}
              onRunSample={() => void runAnalyze()}
            />
          )}

          {showPickHint && (
            <p className="text-sm text-muted-foreground">
              Select a saved recommendation below or run a new analysis.
            </p>
          )}

          {showDetail && engine && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Recommendation</CardTitle>
                <CardDescription>
                  Engine output for {symbol.trim().toUpperCase()}
                  {recId ? (
                    <>
                      {" "}
                      · record <code className="text-xs">{recId}</code>
                    </>
                  ) : null}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <RecommendationDetail
                  symbol={symbol.trim().toUpperCase()}
                  data={engine}
                  recordId={recId}
                  recordStatus={status}
                />

                <Separator />

                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <RecommendationApprovalActions
                    canAct={canApproveReject}
                    loading={approvalLoading}
                    disabled={workflowBusy && !approvalLoading}
                    onApprove={runApprove}
                    onReject={runReject}
                  />
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={!canPersist || workflowBusy}
                      onClick={() => void runPersist()}
                    >
                      {action === "persist" ? "Saving…" : "Save as pending"}
                    </Button>
                    <Button
                      type="button"
                      variant="default"
                      size="sm"
                      disabled={
                        !ready ||
                        !userId ||
                        !recId ||
                        workflowBusy ||
                        status !== "approved"
                      }
                      title={
                        status && status !== "approved"
                          ? "Approve the recommendation first, then submit to Alpaca."
                          : undefined
                      }
                      onClick={() => void runSubmit()}
                    >
                      {action === "submit" ? "Submitting…" : "Submit to broker"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
