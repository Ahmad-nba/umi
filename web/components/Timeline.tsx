import type { Event } from "@/types";

export function Timeline({ events }: { events: Event[] }) {
  return (
    <ol className="space-y-5">
      {events.map((event, index) => (
        <li key={event.id} className="relative flex gap-4">
          <span
            className={`relative z-10 mt-1 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-bold ${index === events.length - 1 ? "bg-coral text-white" : "bg-sage text-white"}`}
          >
            {index + 1}
          </span>
          <div className="min-w-0">
            <p className="ui-sans text-[11px] font-bold uppercase tracking-[.18em] text-muted">
              {new Date(event.created_at).toLocaleString()}
            </p>
            <p className="mt-1 font-semibold">{event.description}</p>
            <p className="ui-sans mt-1 text-sm text-muted">
              {event.event_type.replaceAll("_", " ")}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
