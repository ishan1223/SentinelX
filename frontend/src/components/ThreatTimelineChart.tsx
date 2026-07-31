import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TimelineBucket } from "../hooks/useTelemetryTimeline";
import { formatAbsoluteTime } from "../lib/format";
import { EmptyNotice, LoadingNotice } from "./StateNotice";

const ANOMALY_COLOR = "#d03b3b";

function TimelineTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: TimelineBucket }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const bucket = payload[0].payload;
  return (
    <div className="rounded-md border border-[var(--sx-border)] bg-[var(--sx-surface)] px-3 py-2 text-xs shadow-lg">
      <p className="text-[var(--sx-text-muted)]">{formatAbsoluteTime(bucket.timestamp)}</p>
      <p className="mt-1 font-medium text-[var(--sx-text-primary)]">
        {bucket.anomalous} anomalous / {bucket.total} samples
      </p>
    </div>
  );
}

export function ThreatTimelineChart({
  buckets,
  loading,
  error,
}: {
  buckets: TimelineBucket[];
  loading: boolean;
  error: string | null;
}) {
  if (loading && buckets.length === 0) return <LoadingNotice label="Loading telemetry history…" />;
  if (error && buckets.length === 0) return <EmptyNotice label="Unable to load threat timeline." />;
  if (buckets.length === 0) return <EmptyNotice label="No telemetry recorded yet." />;

  const totalAnomalous = buckets.reduce((sum, b) => sum + b.anomalous, 0);

  return (
    <div>
      <div className="mb-3 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums text-[var(--sx-text-primary)]">
          {totalAnomalous}
        </span>
        <span className="text-xs text-[var(--sx-text-muted)]">
          anomalous events across the fleet in the observed window
        </span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={buckets} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid stroke="var(--sx-grid)" vertical={false} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(v: string) => formatAbsoluteTime(v).split(",")[1]?.trim() ?? v}
            tick={{ fill: "var(--sx-text-muted)", fontSize: 11 }}
            axisLine={{ stroke: "var(--sx-axis)" }}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "var(--sx-text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip content={<TimelineTooltip />} cursor={{ stroke: "var(--sx-axis)" }} />
          <Area
            type="monotone"
            dataKey="anomalous"
            name="Anomalous events"
            stroke={ANOMALY_COLOR}
            strokeWidth={2}
            fill={ANOMALY_COLOR}
            fillOpacity={0.14}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
