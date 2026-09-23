"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { listIssues } from "@/lib/api";
import type { Issue } from "@/types";

export default function HandlerPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    listIssues()
      .then(setIssues)
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Unable to load assigned work.",
        ),
      );
  }, []);
  const open = issues.filter((issue) => issue.status !== "CLOSED");
  return (
    <AppShell section="Handler">
      <div className="mx-auto max-w-7xl px-5 py-10 md:px-10 md:py-14">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
              Assigned work
            </p>
            <h1 className="mt-3 text-5xl leading-none">My feedback queue.</h1>
          </div>
          <div className="ui-sans flex gap-5 text-sm">
            <span>
              <b className="text-2xl">{open.length}</b>
              <br />
              <small className="text-muted">Open</small>
            </span>
            <span>
              <b className="text-2xl">
                {issues.filter((i) => i.status === "IN_PROGRESS").length}
              </b>
              <br />
              <small className="text-muted">In progress</small>
            </span>
          </div>
        </div>
        {error && <p className="mt-8 text-red-700">{error}</p>}
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {issues.map((issue) => (
            <Link
              href={`/handler/tasks/${issue.id}`}
              key={issue.id}
              className="surface-card block transition hover:-translate-y-1 hover:shadow-lg"
            >
              <div className="flex items-start justify-between gap-3">
                <span className="ui-sans text-xs font-bold uppercase tracking-widest text-muted">
                  {issue.reference}
                </span>
                <StatusBadge status={issue.status} />
              </div>
              <h2 className="mt-7 text-2xl">{issue.title}</h2>
              <p className="mt-2 text-muted">{issue.summary}</p>
              <div className="ui-sans mt-7 flex justify-between text-xs font-bold uppercase tracking-wider">
                <span className="text-coral">{issue.priority}</span>
                <span className="text-muted">{issue.department}</span>
              </div>
            </Link>
          ))}
          {!issues.length && !error && (
            <div className="surface-card">
              <p className="text-muted">No assigned feedback yet.</p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
