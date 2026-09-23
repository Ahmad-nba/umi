import Link from "next/link";
import { AppShell } from "@/components/AppShell";

export default function Home() {
  return (
    <AppShell>
      <div className="grain mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl items-center gap-12 px-5 py-12 md:grid-cols-[1.1fr_.9fr] md:px-10 md:py-20">
        <section>
          <p className="ui-sans mb-5 text-xs font-bold uppercase tracking-[.25em] text-coral">
            A clearer loop for UMI
          </p>
          <h1 className="max-w-3xl text-5xl leading-[.95] tracking-tight md:text-7xl">
            From a finding
            <br />
            <em className="text-sage">to a verified fix.</em>
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-muted">
            Feedback Watch Tower gives every QA finding a path, an owner, and a
            visible ending.
          </p>
        </section>
        <section className="rounded-[2rem] border border-line bg-surface p-7 shadow-[0_20px_70px_rgba(45,81,69,.12)] md:p-9">
          <p className="ui-sans text-xs font-bold uppercase tracking-[.2em] text-muted">
            Choose your workspace
          </p>
          <div className="mt-6 space-y-3">
            <Link className="persona-link bg-moss text-white" href="/reporter">
              <span>
                <strong>Reporter</strong>
                <small>Tell UMI what happened</small>
              </span>
              <span>→</span>
            </Link>
            <Link className="persona-link" href="/handler">
              <span>
                <strong>Handler</strong>
                <small>Work on assigned findings</small>
              </span>
              <span>→</span>
            </Link>
            <Link className="persona-link" href="/qa">
              <span>
                <strong>QA Watch Tower</strong>
                <small>See the whole system</small>
              </span>
              <span>→</span>
            </Link>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
