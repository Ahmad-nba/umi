"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { Timeline } from "@/components/Timeline";
import { getIssue, getIssueDetail, workflow } from "@/lib/api";
import type { Issue, IssueDetail } from "@/types";

export default function HandlerTaskPage() {
  const { id } = useParams<{ id: string }>();
  const [issue, setIssue] = useState<Issue | null>(null);
  const [detail, setDetail] = useState<IssueDetail | null>(null);
  const [resolution, setResolution] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      const issueData = await getIssue(Number(id));
      setIssue(issueData);
      setDetail(await getIssueDetail(Number(id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load issue.");
    }
  }
  // The effect synchronizes the route parameter with server state.
  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps
  useEffect(() => {
    load();
  }, [id]);
  async function action(event: FormEvent, name: string, body?: object) {
    event.preventDefault();
    setBusy(true);
    try {
      await workflow(Number(id), name, body);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update issue.");
    } finally {
      setBusy(false);
    }
  }
  if (error)
    return (
      <AppShell section="Handler">
        <div className="mx-auto max-w-3xl px-5 py-20 text-red-700">{error}</div>
      </AppShell>
    );
  if (!issue || !detail)
    return (
      <AppShell section="Handler">
        <div className="mx-auto max-w-3xl px-5 py-20 text-muted">
          Loading issue...
        </div>
      </AppShell>
    );
  return (
    <AppShell section="Handler">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-10 md:py-14">
        <Link href="/handler" className="ui-sans text-sm font-bold text-sage">
          ← Assigned work
        </Link>
        <div className="mt-8 flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
              {issue.reference}
            </p>
            <h1 className="mt-3 text-5xl leading-none">{issue.title}</h1>
          </div>
          <StatusBadge status={issue.status} />
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
          <section className="space-y-6">
            <div className="surface-card">
              <div className="grid gap-5 sm:grid-cols-3">
                <div>
                  <p className="meta-label">Priority</p>
                  <p className="mt-1 font-semibold">{issue.priority}</p>
                </div>
                <div>
                  <p className="meta-label">Category</p>
                  <p className="mt-1 font-semibold">{issue.category}</p>
                </div>
                <div>
                  <p className="meta-label">Department</p>
                  <p className="mt-1 font-semibold">{issue.department}</p>
                </div>
              </div>
              <p className="mt-8 text-lg leading-8">{issue.summary}</p>
            </div>
            <div className="surface-card">
              <h2 className="text-2xl">Lifecycle</h2>
              <div className="mt-6">
                <Timeline events={detail.events} />
              </div>
            </div>
          </section>
          <aside className="surface-card h-fit">
            <h2 className="text-2xl">Next action</h2>
            <p className="mt-3 text-muted">
              {issue.status === "ROUTED"
                ? "Acknowledge and start working on this finding."
                : issue.status === "ACKNOWLEDGED"
                  ? "Start work when you are ready."
                  : issue.status === "IN_PROGRESS"
                    ? "Record the resolution when the fix is ready."
                    : "This issue is awaiting the next lifecycle step."}
            </p>
            {issue.status === "ROUTED" && (
              <button
                disabled={busy}
                onClick={(e) => action(e, "acknowledge")}
                className="button-primary mt-6 w-full"
              >
                Acknowledge
              </button>
            )}
            {issue.status === "ACKNOWLEDGED" && (
              <button
                disabled={busy}
                onClick={(e) => action(e, "start")}
                className="button-primary mt-6 w-full"
              >
                Start work
              </button>
            )}
            {issue.status === "IN_PROGRESS" && (
              <form
                onSubmit={(e) => action(e, "complete", { resolution })}
                className="mt-6 space-y-4"
              >
                <label className="field">
                  <span>Resolution</span>
                  <textarea
                    required
                    minLength={1}
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    rows={5}
                    placeholder="Explain what was fixed."
                  />
                </label>
                <button disabled={busy} className="button-primary w-full">
                  {busy ? "Completing..." : "Mark as completed"}
                </button>
              </form>
            )}
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
