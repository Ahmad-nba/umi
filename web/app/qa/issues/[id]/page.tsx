"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { Timeline } from "@/components/Timeline";
import { getIssueDetail, getNotifications } from "@/lib/api";
import type { IssueDetail, Notification } from "@/types";

export default function QAIssuePage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<IssueDetail | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([getIssueDetail(Number(id)), getNotifications(Number(id))])
      .then(([issueDetail, notificationItems]) => {
        setDetail(issueDetail);
        setNotifications(notificationItems);
      })
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Unable to load issue detail.",
        ),
      );
  }, [id]);
  if (error)
    return (
      <AppShell section="QA">
        <div className="mx-auto max-w-5xl px-5 py-20 text-red-700">{error}</div>
      </AppShell>
    );
  if (!detail)
    return (
      <AppShell section="QA">
        <div className="mx-auto max-w-5xl px-5 py-20 text-muted">
          Loading issue detail...
        </div>
      </AppShell>
    );
  return (
    <AppShell section="QA">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-10 md:py-14">
        <Link href="/qa" className="ui-sans text-sm font-bold text-sage">
          ← Watch Tower
        </Link>
        <div className="mt-8 flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
              Lifecycle inspection
            </p>
            <h1 className="mt-3 text-5xl leading-none">
              {detail.issue.reference}
            </h1>
          </div>
          <StatusBadge status={detail.issue.status} />
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-[1.2fr_.8fr]">
          <section className="surface-card">
            <h2 className="text-2xl">Event timeline</h2>
            <div className="mt-7">
              <Timeline events={detail.events} />
            </div>
          </section>
          <aside className="surface-card h-fit">
            <h2 className="text-2xl">Operational record</h2>
            <dl className="ui-sans mt-6 space-y-4 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Department</dt>
                <dd className="font-bold">{detail.issue.department}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Priority</dt>
                <dd className="font-bold">{detail.issue.priority}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Handler</dt>
                <dd className="font-bold">
                  {detail.issue.handler_id ?? "Unassigned"}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Notifications</dt>
                <dd className="font-bold">{detail.notification_count}</dd>
              </div>
            </dl>
            <h3 className="mt-9 border-t border-line pt-6 text-xl">
              Notifications
            </h3>
            <div className="mt-4 space-y-4">
              {notifications.map((item) => (
                <div key={item.id}>
                  <p className="ui-sans text-xs font-bold uppercase tracking-wider text-muted">
                    {item.event_type}
                  </p>
                  <p className="mt-1 text-sm leading-6">{item.message}</p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
