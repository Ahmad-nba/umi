"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { getDashboard } from "@/lib/api";
import type { Dashboard } from "@/types";

export default function QAPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getDashboard()
      .then(setDashboard)
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Unable to load Watch Tower.",
        ),
      );
  }, []);
  if (error)
    return (
      <AppShell section="QA">
        <div className="mx-auto max-w-5xl px-5 py-20 text-red-700">{error}</div>
      </AppShell>
    );
  if (!dashboard)
    return (
      <AppShell section="QA">
        <div className="mx-auto max-w-5xl px-5 py-20 text-muted">
          Loading Watch Tower...
        </div>
      </AppShell>
    );
  const open = dashboard.issues.filter(
    (issue) => issue.status !== "CLOSED",
  ).length;
  return (
    <AppShell section="QA">
      <div className="mx-auto max-w-7xl px-5 py-10 md:px-10 md:py-14">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
              System overview
            </p>
            <h1 className="mt-3 text-5xl leading-none">Watch Tower.</h1>
          </div>
          <span className="ui-sans text-sm text-muted">
            Live operational view
          </span>
        </div>
        <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="metric-card">
            <span>Total issues</span>
            <strong>{dashboard.total_issues}</strong>
          </div>
          <div className="metric-card">
            <span>Open issues</span>
            <strong>{open}</strong>
          </div>
          <div className="metric-card">
            <span>Awaiting confirmation</span>
            <strong>{dashboard.by_status.AWAITING_CONFIRMATION ?? 0}</strong>
          </div>
          <div className="metric-card accent">
            <span>Closed</span>
            <strong>{dashboard.by_status.CLOSED ?? 0}</strong>
          </div>
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-[.75fr_1.25fr]">
          <section className="surface-card">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl">Lifecycle distribution</h2>
              <span className="ui-sans text-xs uppercase tracking-widest text-muted">
                Issues
              </span>
            </div>
            <div className="mt-6 space-y-4">
              {Object.entries(dashboard.by_status).map(([status, count]) => (
                <div key={status}>
                  <div className="mb-1 flex justify-between ui-sans text-xs font-bold uppercase tracking-wider">
                    <span>{status.replaceAll("_", " ")}</span>
                    <span>{count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-paper">
                    <div
                      className="h-full rounded-full bg-sage"
                      style={{
                        width: `${Math.max(8, (count / Math.max(dashboard.total_issues, 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
          <section className="surface-card">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl">Issues needing attention</h2>
              <span className="ui-sans text-xs uppercase tracking-widest text-muted">
                {dashboard.issues.length} records
              </span>
            </div>
            <div className="mt-5 divide-y divide-line">
              {dashboard.issues.map((issue) => (
                <Link
                  href={`/qa/issues/${issue.id}`}
                  key={issue.id}
                  className="flex items-center justify-between gap-4 py-4 transition hover:pl-2"
                >
                  <div>
                    <p className="ui-sans text-xs font-bold uppercase tracking-widest text-muted">
                      {issue.reference} · {issue.department}
                    </p>
                    <p className="mt-1 font-semibold">{issue.next_action}</p>
                  </div>
                  <StatusBadge status={issue.status} />
                </Link>
              ))}
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
