/**
 * Browser: same-origin proxy (`/api/backend/*` → FastAPI `/api/v1/*`) to avoid CORS.
 * Server: call backend directly when needed.
 */
export function getPublicApiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend";
}

export function getServerApiBase(): string {
  return (
    process.env.API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1"
  );
}
