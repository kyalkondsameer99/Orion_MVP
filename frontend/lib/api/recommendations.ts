import { apiFetch } from "@/lib/api/client";
import type {
  PersistRecommendationRequest,
  RecommendationActionResult,
  RecommendationListResponse,
  RecommendationRequest,
  RecommendationResponse,
  RecommendationSubmitResult,
} from "@/lib/api/types";

export async function analyzeRecommendation(
  body: RecommendationRequest,
): Promise<RecommendationResponse> {
  return apiFetch<RecommendationResponse>("/recommendations/analyze", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type ListRecommendationsParams = {
  status?: string;
  symbol?: string;
  limit?: number;
};

export async function listRecommendations(
  userId: string,
  params?: ListRecommendationsParams,
): Promise<RecommendationListResponse> {
  const sp = new URLSearchParams();
  if (params?.status) sp.set("status", params.status);
  if (params?.symbol) sp.set("symbol", params.symbol);
  if (params?.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  const path = q ? `/recommendations/?${q}` : "/recommendations/";
  return apiFetch<RecommendationListResponse>(path, { method: "GET", userId });
}

export async function persistRecommendation(
  userId: string,
  body: PersistRecommendationRequest,
): Promise<RecommendationActionResult> {
  return apiFetch<RecommendationActionResult>("/recommendations/", {
    method: "POST",
    body: JSON.stringify(body),
    userId,
  });
}

export async function approveRecommendation(
  userId: string,
  recommendationId: string,
): Promise<RecommendationActionResult> {
  return apiFetch<RecommendationActionResult>(
    `/recommendations/${recommendationId}/approve`,
    { method: "POST", userId },
  );
}

export async function rejectRecommendation(
  userId: string,
  recommendationId: string,
): Promise<RecommendationActionResult> {
  return apiFetch<RecommendationActionResult>(
    `/recommendations/${recommendationId}/reject`,
    { method: "POST", userId },
  );
}

export async function submitRecommendation(
  userId: string,
  recommendationId: string,
): Promise<RecommendationSubmitResult> {
  return apiFetch<RecommendationSubmitResult>(
    `/recommendations/${recommendationId}/submit`,
    { method: "POST", userId },
  );
}
