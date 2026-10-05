"use client";

import type { Citation } from "@/lib/api";

/** Renders text with [n] markers as clickable buttons that jump the source
 * viewer to that citation's passage. Unknown/invalid markers (shouldn't
 * happen -- the backend already rejects answers with invented citations --
 * but rendered defensively) are shown as plain text. */
export default function CitedText({
  text,
  citations,
  onCitationClick,
}: {
  text: string;
  citations: Citation[];
  onCitationClick: (citation: Citation) => void;
}) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <span className="whitespace-pre-wrap">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (!match) return <span key={i}>{part}</span>;
        const citation = citations.find((c) => c.index === Number(match[1]));
        if (!citation) return <span key={i}>{part}</span>;
        return (
          <button
            key={i}
            onClick={() => onCitationClick(citation)}
            className="mx-0.5 rounded-sm bg-gold/20 px-1 text-xs font-medium text-navy hover:bg-gold/35"
            title={`${citation.document_filename} — ${citation.section_heading ?? "unlabeled section"}`}
          >
            {part}
          </button>
        );
      })}
    </span>
  );
}
