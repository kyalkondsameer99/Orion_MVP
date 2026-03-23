/** Format engine numeric fields for display. */

export function formatPrice(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}

export function formatConfidence(confidence: number): string {
  return `${(Math.max(0, Math.min(1, confidence)) * 100).toFixed(1)}%`;
}

export function formatRewardRisk(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}
