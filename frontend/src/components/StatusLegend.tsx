import { STATUS_TIER_COLOR, STATUS_TIER_LABEL, type StatusTier } from "../lib/severity";

const ORDER: StatusTier[] = ["normal", "suspicious", "high-risk"];

/** Teaches the app's three-tier status language at a glance -- every
 * status dot anywhere in the app is one of these three colors. */
export function StatusLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-[var(--sx-text-muted)]">
      {ORDER.map((tier) => (
        <span key={tier} className="inline-flex items-center gap-1.5">
          <span
            aria-hidden
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: STATUS_TIER_COLOR[tier] }}
          />
          <span style={{ color: STATUS_TIER_COLOR[tier] }} className="font-medium">
            {STATUS_TIER_LABEL[tier]}
          </span>
        </span>
      ))}
    </div>
  );
}
