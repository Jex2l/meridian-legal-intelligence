"use client";

import type { Citation } from "@/lib/api";

/** A small, clickable numbered badge for an inline [n] citation marker.
 * Jumps the source viewer to the cited passage on click, and shows the
 * source document / section on hover via a lightweight tooltip. Shared by
 * any surface that renders cited model output (currently `CitedText`). */
export default function CitationBadge({
  citation,
  onClick,
}: {
  citation: Citation;
  onClick: (citation: Citation) => void;
}) {
  const location = [citation.section_heading ?? "Unlabeled section", citation.page_number ? `p. ${citation.page_number}` : null]
    .filter(Boolean)
    .join(" · ");

  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        onClick={() => onClick(citation)}
        aria-label={`View source: ${citation.document_filename}, ${location}`}
        className="mx-0.5 inline-flex h-[1.1rem] min-w-[1.1rem] -translate-y-px items-center justify-center rounded-full bg-gold/25 px-1 text-[0.65rem] font-semibold leading-none text-navy ring-1 ring-gold/40 transition hover:bg-gold hover:text-white hover:ring-gold"
      >
        {citation.index}
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 w-max max-w-[16rem] -translate-x-1/2 scale-95 rounded-sm bg-navy px-2.5 py-1.5 text-left text-xs text-white opacity-0 shadow-lg transition group-hover:scale-100 group-hover:opacity-100"
      >
        <span className="block truncate font-medium">{citation.document_filename}</span>
        <span className="block text-white/60">{location}</span>
        <span className="absolute left-1/2 top-full h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rotate-45 bg-navy" />
      </span>
    </span>
  );
}
