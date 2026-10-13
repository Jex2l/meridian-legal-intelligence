"use client";

import type { Citation } from "@/lib/api";
import CitationBadge from "./CitationBadge";

/** Renders text with [n] markers as clickable citation badges that jump the
 * source viewer to that citation's passage. Unknown/invalid markers
 * (shouldn't happen -- the backend already rejects answers with invented
 * citations -- but rendered defensively) are shown as plain text. */
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
    <span className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (!match) return <span key={i}>{part}</span>;
        const citation = citations.find((c) => c.index === Number(match[1]));
        if (!citation) return <span key={i}>{part}</span>;
        return <CitationBadge key={i} citation={citation} onClick={onCitationClick} />;
      })}
    </span>
  );
}
