import Link from "next/link";

export function AppShell({
  children,
  section,
}: {
  children: React.ReactNode;
  section?: string;
}) {
  return (
    <div className="min-h-screen bg-paper">
      <header className="ui-sans border-b border-line bg-surface/90 px-5 py-4 backdrop-blur md:px-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-moss text-sm font-bold text-white">
              U
            </span>
            <span>
              <span className="block text-xs font-bold uppercase tracking-[.22em] text-sage">
                UMI
              </span>
              <span className="block text-sm font-semibold">
                Feedback Watch Tower
              </span>
            </span>
          </Link>
          {section && (
            <span className="rounded-full border border-line px-3 py-1 text-xs font-bold uppercase tracking-widest text-muted">
              {section}
            </span>
          )}
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
