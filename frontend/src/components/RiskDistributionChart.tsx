import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RiskResponse } from "../lib/api";
import { SEVERITY_COLOR, SEVERITY_LABEL, normalizeSeverity, type SeverityTier } from "../lib/severity";
import { EmptyNotice, LoadingNotice } from "./StateNotice";

const TIERS: SeverityTier[] = ["low", "medium", "high", "critical"];

export function RiskDistributionChart({
  risks,
  loading,
}: {
  risks: Record<string, RiskResponse>;
  loading: boolean;
}) {
  const values = Object.values(risks);

  if (loading && values.length === 0) return <LoadingNotice label="Loading risk distribution…" />;
  if (values.length === 0) return <EmptyNotice label="No endpoint risk data yet." />;

  // The count is folded into the axis label text itself ("Low · 4") rather
  // than relying on the bar's own geometry to communicate it: Recharts
  // renders literally nothing for a zero-length bar (no bar, no label),
  // which reads as a missing row rather than "zero". Axis tick text always
  // renders regardless of the bar's value, so this is the one placement
  // that is guaranteed visible for every count, including zero.
  const counts = TIERS.map((tier) => {
    const count = values.filter((r) => normalizeSeverity(r.severity) === tier).length;
    return { tier, count, axisLabel: `${SEVERITY_LABEL[tier]} · ${count}` };
  });
  const maxCount = Math.max(1, ...counts.map((c) => c.count));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={counts} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <XAxis type="number" allowDecimals={false} hide domain={[0, maxCount]} />
        <YAxis
          type="category"
          dataKey="axisLabel"
          tick={{ fill: "var(--sx-text-secondary)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={88}
        />
        <Tooltip
          cursor={{ fill: "rgba(255,255,255,0.04)" }}
          content={({ active, payload }) => {
            if (!active || !payload || payload.length === 0) return null;
            const entry = payload[0].payload as (typeof counts)[number];
            return (
              <div className="rounded-md border border-[var(--sx-border)] bg-[var(--sx-surface)] px-3 py-2 text-xs shadow-lg">
                <span className="font-medium text-[var(--sx-text-primary)]">
                  {SEVERITY_LABEL[entry.tier]}: {entry.count} endpoint{entry.count === 1 ? "" : "s"}
                </span>
              </div>
            );
          }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={22} isAnimationActive={false}>
          {counts.map((entry) => (
            <Cell key={entry.tier} fill={SEVERITY_COLOR[entry.tier]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
