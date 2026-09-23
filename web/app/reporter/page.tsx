import Link from "next/link";
import { AppShell } from "@/components/AppShell";

export default function ReporterPage() {
  return (
    <AppShell section="Reporter">
      <div className="mx-auto max-w-6xl px-5 py-12 md:px-10 md:py-20">
        <div className="max-w-3xl">
          <p className="ui-sans text-xs font-bold uppercase tracking-[.25em] text-coral">
            Your voice has a route
          </p>
          <h1 className="mt-5 text-5xl leading-none md:text-7xl">
            Tell us what happened.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-muted">
            Your feedback helps UMI identify problems, route them to the
            responsible team, and improve services.
          </p>
        </div>
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          <div className="info-card">
            <span className="step-no">01</span>
            <h2>We listen</h2>
            <p>Describe the thing that felt wrong, incomplete, or confusing.</p>
          </div>
          <div className="info-card">
            <span className="step-no">02</span>
            <h2>We route</h2>
            <p>UMI structures your finding and sends it to the right team.</p>
          </div>
          <div className="info-card">
            <span className="step-no">03</span>
            <h2>We close the loop</h2>
            <p>You can see what happened and confirm whether it was fixed.</p>
          </div>
        </div>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link className="button-primary" href="/reporter/feedback">
            Give feedback <span>→</span>
          </Link>
          <details className="ui-sans text-sm text-muted">
            <summary className="cursor-pointer font-bold text-ink">
              Why are we collecting this?
            </summary>
            <p className="mt-3 max-w-md leading-6">
              Your report becomes a structured QA finding. Your contact is used
              only to connect updates to your feedback.
            </p>
          </details>
        </div>
      </div>
    </AppShell>
  );
}
