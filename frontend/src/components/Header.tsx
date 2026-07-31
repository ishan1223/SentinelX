import { formatRelativeTime } from "../lib/format";

export type ViewMode = "dashboard" | "demo";

export function Header({
  mode,
  onChangeMode,
  lastUpdated,
  refreshing,
  simulationPending,
  simulationMessage,
  onSimulateCompromise,
  onResetSimulation,
}: {
  mode: ViewMode;
  onChangeMode: (mode: ViewMode) => void;
  lastUpdated: Date | null;
  refreshing: boolean;
  simulationPending: boolean;
  simulationMessage: string | null;
  onSimulateCompromise: () => void;
  onResetSimulation: () => void;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-[var(--sx-border)] bg-[var(--sx-page)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <div>
            <div className="flex items-center gap-2.5">
              <span
                aria-hidden
                className="flex h-7 w-7 items-center justify-center rounded border border-[var(--sx-accent)]/40 bg-[var(--sx-accent)]/15 text-xs font-bold text-[var(--sx-accent)]"
              >
                SX
              </span>
              <h1 className="text-lg font-semibold tracking-tight text-[var(--sx-text-primary)]">
                SENTINEL<span className="text-[var(--sx-accent)]">X</span>
              </h1>
            </div>
            <p className="mt-0.5 text-xs text-[var(--sx-text-muted)]">
              Behavioural Threat Intelligence &amp; Compromise Detection
            </p>
          </div>

          <div
            role="tablist"
            aria-label="View"
            className="flex items-center gap-1 rounded-md border border-[var(--sx-border)] p-0.5"
          >
            {(["dashboard", "demo"] as const).map((m) => (
              <button
                key={m}
                type="button"
                role="tab"
                aria-selected={mode === m}
                onClick={() => onChangeMode(m)}
                className={`rounded px-3 py-1.5 text-xs font-medium transition ${
                  mode === m
                    ? "bg-[var(--sx-accent)]/20 text-[var(--sx-accent)]"
                    : "text-[var(--sx-text-muted)] hover:text-[var(--sx-text-primary)]"
                }`}
              >
                {m === "dashboard" ? "Dashboard" : "Demo Mode"}
              </button>
            ))}
          </div>
        </div>

        {mode === "dashboard" && (
          <div className="flex items-center gap-3">
            <div className="hidden text-right text-xs text-[var(--sx-text-muted)] sm:block">
              {refreshing ? (
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--sx-accent)]" />
                  Refreshing…
                </span>
              ) : lastUpdated ? (
                <span>Updated {formatRelativeTime(lastUpdated.toISOString())}</span>
              ) : null}
            </div>

            <button
              type="button"
              onClick={onResetSimulation}
              disabled={simulationPending}
              className="rounded-md border border-[var(--sx-border)] bg-transparent px-3.5 py-2 text-sm font-medium text-[var(--sx-text-secondary)] transition hover:border-[var(--sx-text-secondary)] hover:text-[var(--sx-text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              Reset Simulation
            </button>
            <button
              type="button"
              onClick={onSimulateCompromise}
              disabled={simulationPending}
              className="rounded-md border border-[#d03b3b66] bg-[#d03b3b1f] px-3.5 py-2 text-sm font-semibold text-[#f0958a] transition hover:bg-[#d03b3b33] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {simulationPending ? "Working…" : "Simulate Compromise"}
            </button>
          </div>
        )}
      </div>

      {simulationMessage && (
        <div className="mx-auto max-w-[1400px] px-6 pb-3" role="status" aria-live="polite">
          <div className="rounded-md border border-[var(--sx-accent)]/30 bg-[var(--sx-accent)]/10 px-3 py-2 text-xs text-[var(--sx-text-secondary)]">
            {simulationMessage}
          </div>
        </div>
      )}
    </header>
  );
}
