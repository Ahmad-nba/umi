"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { createFeedback, routeFeedback } from "@/lib/api";

export default function FeedbackPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    content: "",
    name: "",
    contact: "",
    context: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const feedback = await createFeedback({ ...form, channel: "web" });
      await routeFeedback(feedback.id);
      router.push(`/reporter/feedback/${feedback.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setBusy(false);
    }
  }
  return (
    <AppShell section="Reporter">
      <div className="mx-auto max-w-3xl px-5 py-10 md:px-10 md:py-16">
        <Link className="ui-sans text-sm font-bold text-sage" href="/reporter">
          ← Back to purpose
        </Link>
        <div className="mt-8">
          <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
            New finding
          </p>
          <h1 className="mt-4 text-5xl leading-none">
            What would you like UMI to know?
          </h1>
          <p className="mt-5 text-muted">
            Start with what happened. The Watch Tower will do the organizing.
          </p>
        </div>
        <form
          onSubmit={submit}
          className="mt-9 space-y-6 rounded-[2rem] border border-line bg-surface p-6 shadow-sm md:p-9"
        >
          <label className="field">
            <span>Your feedback</span>
            <textarea
              required
              minLength={1}
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              placeholder="My Engineering Mathematics marks are missing from the portal."
              rows={6}
            />
          </label>
          <div className="grid gap-5 md:grid-cols-2">
            <label className="field">
              <span>Your name</span>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Grace Namara"
              />
            </label>
            <label className="field">
              <span>Email for updates</span>
              <input
                required
                type="email"
                value={form.contact}
                onChange={(e) => setForm({ ...form, contact: e.target.value })}
                placeholder="grace@example.com"
              />
            </label>
          </div>
          <label className="field">
            <span>Optional context</span>
            <input
              value={form.context}
              onChange={(e) => setForm({ ...form, context: e.target.value })}
              placeholder="Semester 2 results were recently released"
            />
          </label>
          {error && (
            <p className="ui-sans rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}
          <button
            className="button-primary w-full justify-center"
            disabled={busy}
          >
            {busy ? "Sending your feedback..." : "Send feedback →"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}
