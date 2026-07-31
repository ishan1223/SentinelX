import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  action,
  children,
  className = "",
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] ${className}`}
    >
      <header className="flex items-start justify-between gap-3 border-b border-[var(--sx-border)] px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-[var(--sx-text-primary)]">
            {title}
          </h2>
          {subtitle && (
            <p className="mt-0.5 text-xs text-[var(--sx-text-muted)]">{subtitle}</p>
          )}
        </div>
        {action}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}
