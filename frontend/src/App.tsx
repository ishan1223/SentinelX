import { useState } from "react";
import { DemoMode } from "./components/DemoMode";
import { EndpointTable } from "./components/EndpointTable";
import { Header, type ViewMode } from "./components/Header";
import { InvestigationPanel } from "./components/InvestigationPanel";
import { Panel } from "./components/Panel";
import { RecentIncidents } from "./components/RecentIncidents";
import { RiskDistributionChart } from "./components/RiskDistributionChart";
import { ErrorNotice, LoadingNotice } from "./components/StateNotice";
import { StatusLegend } from "./components/StatusLegend";
import { SummaryCards } from "./components/SummaryCards";
import { ThreatTimelineChart } from "./components/ThreatTimelineChart";
import { ValueProps } from "./components/ValueProps";
import { useDashboardData } from "./hooks/useDashboardData";
import { useTelemetryTimeline } from "./hooks/useTelemetryTimeline";

export default function App() {
  const {
    endpoints,
    risks,
    incidents,
    loading,
    refreshing,
    error,
    lastUpdated,
    simulationPending,
    simulationMessage,
    simulateCompromise,
    resetSimulation,
  } = useDashboardData();

  const [selectedHostname, setSelectedHostname] = useState<string | null>(null);
  const [mode, setMode] = useState<ViewMode>("dashboard");

  const refreshToken = lastUpdated?.getTime() ?? 0;
  const timeline = useTelemetryTimeline(endpoints, refreshToken);

  const selectedEndpoint = endpoints.find((e) => e.id === selectedHostname);

  return (
    <div className="min-h-screen bg-[var(--sx-page)] text-[var(--sx-text-secondary)]">
      <Header
        mode={mode}
        onChangeMode={setMode}
        lastUpdated={lastUpdated}
        refreshing={refreshing}
        simulationPending={simulationPending}
        simulationMessage={simulationMessage}
        onSimulateCompromise={simulateCompromise}
        onResetSimulation={resetSimulation}
      />

      {loading && (
        <div className="flex justify-center py-16">
          <LoadingNotice label="Connecting to SentinelX backend…" />
        </div>
      )}

      {error && !loading && (
        <div className="mx-auto max-w-[1400px] px-6 pt-6">
          <ErrorNotice label={`Backend unreachable: ${error}`} />
        </div>
      )}

      {!loading && mode === "demo" && <DemoMode endpoints={endpoints} risks={risks} />}

      {!loading && mode === "dashboard" && (
        <main className="mx-auto max-w-[1400px] space-y-5 px-6 py-6">
          <ValueProps />

          <SummaryCards endpoints={endpoints} risks={risks} incidents={incidents} />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <Panel
              title="Threat Activity Timeline"
              subtitle="Anomalous telemetry events across the fleet"
              className="lg:col-span-2"
            >
              <ThreatTimelineChart
                buckets={timeline.buckets}
                loading={timeline.loading}
                error={timeline.error}
              />
            </Panel>

            <Panel title="Endpoint Risk Distribution" subtitle="Current severity across the fleet">
              <RiskDistributionChart risks={risks} loading={loading} />
            </Panel>
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <Panel title="Recent Incidents" subtitle="Latest detections, most recent first" className="lg:col-span-1">
              <RecentIncidents incidents={incidents} onSelectHost={setSelectedHostname} />
            </Panel>

            <Panel
              title="Endpoint Health"
              subtitle="Click a row to open the investigation view"
              action={<StatusLegend />}
              className="lg:col-span-2"
            >
              <EndpointTable
                endpoints={endpoints}
                risks={risks}
                loading={loading}
                onSelectHost={setSelectedHostname}
              />
            </Panel>
          </div>
        </main>
      )}

      {selectedHostname && (
        <InvestigationPanel
          hostname={selectedHostname}
          endpoint={selectedEndpoint}
          refreshToken={refreshToken}
          onClose={() => setSelectedHostname(null)}
        />
      )}
    </div>
  );
}
