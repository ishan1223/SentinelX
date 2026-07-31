/**
 * Central severity <-> color/label mapping. Maps backend severity tiers
 * (low/medium/high/critical) to standardized status colors for the UI.
 */

export type SeverityTier = "low" | "medium" | "high" | "critical";

export const SEVERITY_COLOR: Record<SeverityTier, string> = {
  low: "#0ca30c",
  medium: "#fab219",
  high: "#ec835a",
  critical: "#d03b3b",
};

export const SEVERITY_LABEL: Record<SeverityTier, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export function normalizeSeverity(value: string): SeverityTier {
  const lower = value.toLowerCase();
  if (lower === "low" || lower === "medium" || lower === "high" || lower === "critical") {
    return lower;
  }
  return "low";
}

export function severityColor(value: string): string {
  return SEVERITY_COLOR[normalizeSeverity(value)];
}

export function severityLabel(value: string): string {
  return SEVERITY_LABEL[normalizeSeverity(value)];
}

/** Two-bucket health classification used by summary cards + table status. */
export function isHealthy(severity: string): boolean {
  return normalizeSeverity(severity) === "low";
}

/**
 * The primary at-a-glance status vocabulary: every severity in the app
 * collapses to exactly one of these three bands, each with its own color
 * so NORMAL / SUSPICIOUS / HIGH RISK are always visually unambiguous.
 * medium and high both read as "suspicious" -- the distinction between
 * them still shows up as the precise SeverityBadge in detail views
 * (investigation panel, incidents), but a scanning glance only needs
 * three buckets, not four.
 */
export type StatusTier = "normal" | "suspicious" | "high-risk";

export const STATUS_TIER_COLOR: Record<StatusTier, string> = {
  normal: SEVERITY_COLOR.low,
  suspicious: SEVERITY_COLOR.medium,
  "high-risk": SEVERITY_COLOR.critical,
};

export const STATUS_TIER_LABEL: Record<StatusTier, string> = {
  normal: "Normal",
  suspicious: "Suspicious",
  "high-risk": "High Risk",
};

export function statusTier(severity: string): StatusTier {
  const tier = normalizeSeverity(severity);
  if (tier === "low") return "normal";
  if (tier === "critical") return "high-risk";
  return "suspicious";
}

export function statusTierColor(severity: string): string {
  return STATUS_TIER_COLOR[statusTier(severity)];
}

export function statusTierLabel(severity: string): string {
  return STATUS_TIER_LABEL[statusTier(severity)];
}
