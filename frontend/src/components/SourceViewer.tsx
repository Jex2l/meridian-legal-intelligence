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
      <div className="flex h-full items-center justify-center bg-white text-sm text-navy/40">
        Select a document, or click a citation, to view the source.
      </div>
    );
  }

  if (error) {
    return <div className="p-6 text-sm text-red-600">{error}</div>;
  }

  if (!detail) {
    return <div className="p-6 text-sm text-navy/40">Loading...</div>;
  }

  return (
    <div className="h-full overflow-y-auto bg-white p-6">
      <h2 className="font-serif-brand mb-1 text-lg font-semibold text-navy">{detail.filename}</h2>
      {detail.jurisdiction && <p className="mb-4 text-xs text-navy/40">Jurisdiction: {detail.jurisdiction}</p>}
      <div className="space-y-4">
        {detail.chunks.map((chunk) => (
          <div
            key={chunk.id}
            ref={(el) => {
              chunkRefs.current[chunk.id] = el;
            }}
            className={`rounded-sm border p-3 text-sm transition-colors ${
              chunk.id === highlightChunkId
                ? "border-gold bg-gold/10"
                : "border-navy/10 bg-white"
            }`}
          >
            {chunk.section_heading && (
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-navy/50">
                {chunk.section_heading}
                {chunk.page_number ? ` · page ${chunk.page_number}` : ""}
              </p>
            )}
            <p className="whitespace-pre-wrap text-navy/80">{chunk.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
