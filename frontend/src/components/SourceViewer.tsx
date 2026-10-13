"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentDetail } from "@/lib/api";

export default function SourceViewer({
  token,
  documentId,
  highlightChunkId,
}: {
  token: string;
  documentId: string | null;
  highlightChunkId: string | null;
}) {
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const chunkRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (!documentId) {
      setDetail(null);
      return;
    }
    setError(null);
    setDetail(null);
    api
      .getDocument(token, documentId)
      .then(setDetail)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load document"));
  }, [token, documentId]);

  useEffect(() => {
    if (highlightChunkId && chunkRefs.current[highlightChunkId]) {
      chunkRefs.current[highlightChunkId]?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [highlightChunkId, detail]);

  if (!documentId) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-white px-6 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-navy-pale">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-navy/50">
            <path
              d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
            <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
          </svg>
        </div>
        <p className="text-sm font-medium text-navy/70">No source selected</p>
        <p className="mt-1 max-w-xs text-xs text-navy/40">
          Select a document from the left, or click a numbered citation in the chat to jump straight to the passage it
          cites.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="flex items-center gap-1.5 text-sm text-red-600">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
            <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
            <path d="M12 8v5M12 16h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          {error}
        </p>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="h-full overflow-y-auto bg-white p-6">
        <div className="mb-4 h-5 w-2/3 animate-pulse rounded-sm bg-navy-pale" />
        <div className="mb-6 h-3 w-1/3 animate-pulse rounded-sm bg-navy-pale" />
        <div className="space-y-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="rounded-sm border border-navy/10 p-3">
              <div className="mb-2 h-3 w-1/4 animate-pulse rounded-sm bg-navy-pale" />
              <div className="h-3 w-full animate-pulse rounded-sm bg-navy-pale" />
              <div className="mt-1.5 h-3 w-5/6 animate-pulse rounded-sm bg-navy-pale" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-white p-6">
      <div className="mb-5 border-b border-navy/10 pb-4">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-navy/40">Source document</p>
        <h2 className="font-serif-brand text-lg font-semibold text-navy">{detail.filename}</h2>
        {detail.jurisdiction && <p className="mt-1 text-xs text-navy/40">Jurisdiction: {detail.jurisdiction}</p>}
      </div>
      <div className="space-y-3">
        {detail.chunks.map((chunk) => {
          const isHighlighted = chunk.id === highlightChunkId;
          return (
            <div
              key={chunk.id}
              ref={(el) => {
                chunkRefs.current[chunk.id] = el;
              }}
              className={`rounded-sm border-l-2 p-3 text-sm transition-colors ${
                isHighlighted ? "border-l-gold bg-gold/10" : "border-l-navy/10 bg-white hover:border-l-navy/25"
              }`}
            >
              <div className="mb-1.5 flex items-center justify-between gap-2">
                {chunk.section_heading ? (
                  <p className="truncate text-xs font-semibold uppercase tracking-wide text-navy/50">
                    {chunk.section_heading}
                  </p>
                ) : (
                  <p className="text-xs font-semibold uppercase tracking-wide text-navy/30">Unlabeled section</p>
                )}
                {chunk.page_number ? (
                  <span className="flex-shrink-0 rounded-full bg-navy-pale px-2 py-0.5 text-[0.65rem] font-medium text-navy/50">
                    p. {chunk.page_number}
                  </span>
                ) : null}
              </div>
              {isHighlighted && (
                <p className="mb-1.5 flex items-center gap-1 text-[0.65rem] font-medium uppercase tracking-wide text-gold">
                  <span className="h-1.5 w-1.5 rounded-full bg-gold" /> Cited passage
                </p>
              )}
              <p className="whitespace-pre-wrap leading-relaxed text-navy/80">{chunk.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
