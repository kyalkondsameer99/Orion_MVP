import { apiFetch } from "@/lib/api/client";
import type {
  WatchlistItemCreate,
  WatchlistItemRead,
  WatchlistListResponse,
} from "@/lib/api/types";

export async function listWatchlist(userId: string): Promise<WatchlistListResponse> {
  return apiFetch<WatchlistListResponse>("/watchlist", { userId });
}

export async function addWatchlistItem(
  userId: string,
  body: WatchlistItemCreate,
): Promise<WatchlistItemRead> {
  return apiFetch<WatchlistItemRead>("/watchlist", {
    method: "POST",
    body: JSON.stringify(body),
    userId,
  });
}

export async function removeWatchlistItem(userId: string, symbol: string): Promise<void> {
  const enc = encodeURIComponent(symbol);
  await apiFetch<void>(`/watchlist/${enc}`, { method: "DELETE", userId });
}
