const PROPS = [
  {
    lead: "IoC-independent",
    detail: "Flags behaviour that deviates from a host's own learned baseline — not known-bad signatures.",
  },
  {
    lead: "Multi-signal correlation",
    detail: "A single unusual metric is noise. Risk only escalates when independent signals move together.",
  },
  {
    lead: "Explainable",
    detail: "Every score traces to the real evidence behind it — observed value, baseline, deviation.",
  },
];

/** Slim, text-only strip so a judge grasps the three differentiators in
 * the first few seconds, without reading behaviour to infer them. */
export function ValueProps() {
  return (
    <div className="grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-[var(--sx-border)] bg-[var(--sx-border)] sm:grid-cols-3">
      {PROPS.map((prop) => (
        <div key={prop.lead} className="bg-[var(--sx-surface)] px-4 py-3">
          <p className="text-xs font-semibold text-[var(--sx-accent)]">{prop.lead}</p>
          <p className="mt-0.5 text-xs leading-relaxed text-[var(--sx-text-muted)]">{prop.detail}</p>
        </div>
      ))}
    </div>
  );
}
