export function LoadingNotice({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2.5 py-6 text-sm text-[var(--sx-text-muted)]">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--sx-border)] border-t-[var(--sx-accent)]" />
      {label}
    </div>
  );
}

export function EmptyNotice({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-8 text-center">
      <p className="text-sm text-[var(--sx-text-secondary)]">{label}</p>
    </div>
  );
}

export function ErrorNotice({ label }: { label: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-md border border-[#d03b3b40] bg-[#d03b3b14] px-3 py-2.5 text-sm text-[#ec835a]">
      <span aria-hidden className="mt-0.5">
        ⚠
      </span>
      <span>{label}</span>
    </div>
  );
}
