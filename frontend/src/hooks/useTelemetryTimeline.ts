import { useEffect, useState } from "react";
import { fetchTelemetry, type EndpointItem } from "../lib/api";

export interface TimelineBucket {
  timestamp: string;
  total: number;
  anomalous: number;
}

export function useTelemetryTimeline(endpoints: EndpointItem[], refreshToken: number) {
  const [buckets, setBuckets] = useState<TimelineBucket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (endpoints.length === 0) {
      setLoading(false);
      return;
    }
    let cancelled = false;

    async function load() {
      try {
        const results = await Promise.allSettled(
          endpoints.map((e) => fetchTelemetry(e.id, 40)),
        );

        const byTimestamp = new Map<string, TimelineBucket>();
        for (const result of results) {
          if (result.status !== "fulfilled") continue;
          for (const sample of result.value.samples) {
            const existing = byTimestamp.get(sample.timestamp);
            if (existing) {
              existing.total += 1;
              if (sample.is_anomalous) existing.anomalous += 1;
            } else {
              byTimestamp.set(sample.timestamp, {
                timestamp: sample.timestamp,
                total: 1,
                anomalous: sample.is_anomalous ? 1 : 0,
              });
            }
          }
        }

        const sorted = Array.from(byTimestamp.values()).sort((a, b) =>
          a.timestamp.localeCompare(b.timestamp),
        );

        if (!cancelled) {
          setBuckets(sorted.slice(-40));
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load telemetry timeline");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [endpoints, refreshToken]);

  return { buckets, loading, error };
}
