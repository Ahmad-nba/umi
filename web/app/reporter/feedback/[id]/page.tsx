"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { Timeline } from "@/components/Timeline";
import {
  getFeedback,
  getIssueDetail,
  getNotifications,
  listIssues,
  workflow,
} from "@/lib/api";
import type { Feedback, IssueDetail, Notification } from "@/types";

export default function ReporterStatusPage() {
  const { id } = useParams<{ id: string }>();
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [detail, setDetail] = useState<IssueDetail | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      const item = await getFeedback(Number(id));
      setFeedback(item);
      const issues = await listIssues();
      const issue = issues.find(
        (candidate) => candidate.feedback_id === Number(id),
      );
      if (issue) {
        setDetail(await getIssueDetail(issue.id));
        setNotifications(await getNotifications(issue.id));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load feedback.");
    }
  }
  // The effect synchronizes the route parameter with server state.
  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps
  useEffect(() => {
    load();
  }, [id]);
  async function confirm(confirmed: boolean) {
    if (!detail) return;
    setBusy(true);
    try {
      await workflow(detail.issue.id, "confirm", { confirmed });
      if (confirmed) await workflow(detail.issue.id, "close");
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to update the issue.",
      );
    } finally {
      setBusy(false);
    }
  }
  if (error)
    return (
      <AppShell section="Reporter">
        <div className="mx-auto max-w-3xl px-5 py-20">
          <p className="ui-sans text-red-700">{error}</p>
        </div>
      </AppShell>
    );
  if (!feedback)
    return (
      <AppShell section="Reporter">
        <div className="mx-auto max-w-3xl px-5 py-20">
          <p className="ui-sans text-muted">Loading your feedback...</p>
        </div>
      </AppShell>
    );
  return (
    <AppShell section="Reporter">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-10 md:py-16">
        <Link className="ui-sans text-sm font-bold text-sage" href="/reporter">
          ← Reporter home
        </Link>
        <div className="mt-8 flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
              Your feedback
            </p>
            <h1 className="mt-3 text-5xl leading-none">
              Feedback #{feedback.id}
            </h1>
          </div>
          {detail && <StatusBadge status={detail.issue.status} />}
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
          <section className="space-y-6">
            <div className="surface-card">
              <p className="ui-sans text-xs font-bold uppercase tracking-widest text-muted">
                You told us
              </p>
              <p className="mt-4 text-xl leading-8">{feedback.content}</p>
              {feedback.context && (
                <p className="mt-4 ui-sans text-sm text-muted">
                  Context: {feedback.context}
                </p>
              )}
            </div>
            {detail ? (
              <div className="surface-card">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl">What happened</h2>
                  <span className="ui-sans text-sm text-muted">
                    {detail.issue.department}
                  </span>
                </div>
                <p className="mt-3 text-muted">{detail.issue.next_action}</p>
                <div className="mt-7">
                  <Timeline events={detail.events} />
                </div>
                {detail.issue.status === "AWAITING_CONFIRMATION" && (
                  <div className="mt-8 border-t border-line pt-6">
                    <h3 className="text-2xl">Has this been resolved?</h3>
                    <p className="mt-2 text-muted">
                      Check the issue detail for the resolution and confirm the
                      result.
                    </p>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <button
                        disabled={busy}
                        onClick={() => confirm(true)}
                        className="button-primary"
                      >
                        Yes, it&apos;s resolved
                      </button>
                      <button
                        disabled={busy}
                        onClick={() => confirm(false)}
                        className="button-secondary"
                      >
                        I still need help
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="surface-card">
                <p className="text-muted">Your feedback is being processed.</p>
              </div>
            )}
          </section>
          <aside className="surface-card h-fit">
            <h2 className="text-2xl">Updates</h2>
            <div className="mt-5 space-y-4">
              {notifications.length ? (
                notifications.map((item) => (
                  <div key={item.id} className="border-l-2 border-sun pl-4">
                    <p className="ui-sans text-xs font-bold uppercase tracking-wider text-muted">
                      {item.event_type.replaceAll("_", " ")}
                    </p>
                    <p className="mt-1 text-sm leading-6">{item.message}</p>
                  </div>
                ))
              ) : (
                <p className="text-muted">No updates yet.</p>
              )}
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
