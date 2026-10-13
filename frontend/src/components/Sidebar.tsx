"use client";

import { useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentOut } from "@/lib/api";
import Logo from "./Logo";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function StatusDot({ status }: { status: string }) {
  const color = status === "ready" ? "bg-emerald-500" : status === "failed" ? "bg-red-500" : "bg-amber-400";
  return <span className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${color}`} title={status} />;
}

export default function Sidebar({
  token,
  documents,
  selectedDocumentId,
  onSelectDocument,
  onUploaded,
  workspaceName,
  onLogout,
}: {
  token: string;
  documents: DocumentOut[];
  selectedDocumentId: string | null;
  onSelectDocument: (id: string) => void;
  onUploaded: () => void;
  workspaceName: string;
  onLogout: () => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(token, file);
      onUploaded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  return (
    <aside className="flex h-full w-72 flex-shrink-0 flex-col border-r border-navy/10 bg-navy-pale">
      <div className="border-b border-navy/10 p-4">
        <Logo className="scale-90" />
      </div>

      <div className="flex items-center gap-2.5 border-b border-navy/10 p-4">
        <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-navy text-xs font-semibold text-white">
          {initials(workspaceName)}
        </span>
        <div className="min-w-0">
          <p className="text-[0.65rem] uppercase tracking-wide text-navy/40">Workspace</p>
          <p className="truncate text-sm font-semibold text-navy">{workspaceName}</p>
        </div>
      </div>

      <div className="border-b border-navy/10 p-4">
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-navy/25 bg-white px-3 py-2.5 text-center text-sm text-navy/70 transition hover:border-gold hover:bg-gold/5 hover:text-navy"
        >
          {uploading ? (
            <>
              <svg className="h-3.5 w-3.5 animate-spin text-navy/50" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity="0.25" />
                <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              Uploading...
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
                <path d="M12 4v12M6 10l6-6 6 6M5 20h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Upload PDF / DOCX
            </>
          )}
        </label>
        {error && (
          <p className="mt-2 flex items-start gap-1 text-xs text-red-600">
            <span className="mt-0.5 h-1 w-1 flex-shrink-0 rounded-full bg-red-600" />
            {error}
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <p className="px-2 pb-1 pt-2 text-[0.65rem] font-medium uppercase tracking-wide text-navy/40">
          Documents {documents.length > 0 && `(${documents.length})`}
        </p>
        {documents.length === 0 && (
          <p className="px-2 py-4 text-sm text-navy/40">No documents yet. Upload one to get started.</p>
        )}
        <ul className="space-y-0.5">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                onClick={() => onSelectDocument(doc.id)}
                className={`flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition ${
                  selectedDocumentId === doc.id ? "bg-navy text-white" : "text-navy/80 hover:bg-white"
                }`}
                title={doc.filename}
              >
                <span className="flex-shrink-0 text-xs">{doc.source_type === "public_corpus" ? "🌐" : "📄"}</span>
                <span className="min-w-0 flex-1 truncate">{doc.filename}</span>
                {doc.source_type !== "public_corpus" && <StatusDot status={doc.status} />}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="border-t border-navy/10 p-4">
        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 text-xs text-navy/40 transition hover:text-navy"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
            <path
              d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Log out
        </button>
      </div>
    </aside>
  );
}
