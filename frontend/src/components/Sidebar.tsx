"use client";

import { useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentOut } from "@/lib/api";
import Logo from "./Logo";

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
    <aside className="flex h-full w-72 flex-col border-r border-navy/10 bg-navy-pale">
      <div className="border-b border-navy/10 p-4">
        <Logo className="scale-90" />
      </div>

      <div className="border-b border-navy/10 p-4">
        <p className="text-xs uppercase tracking-wide text-navy/40">Workspace</p>
        <p className="truncate text-sm font-semibold text-navy">{workspaceName}</p>
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
          className="block w-full cursor-pointer rounded-sm border border-dashed border-navy/25 bg-white px-3 py-2 text-center text-sm text-navy/70 transition hover:border-gold hover:text-navy"
        >
          {uploading ? "Uploading..." : "+ Upload PDF / DOCX"}
        </label>
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <p className="px-2 pb-1 pt-2 text-xs uppercase tracking-wide text-navy/40">Documents</p>
        {documents.length === 0 && (
          <p className="px-2 py-4 text-sm text-navy/40">No documents yet. Upload one to get started.</p>
        )}
        <ul className="space-y-1">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                onClick={() => onSelectDocument(doc.id)}
                className={`block w-full truncate rounded-sm px-2 py-2 text-left text-sm transition ${
                  selectedDocumentId === doc.id ? "bg-navy text-white" : "text-navy/80 hover:bg-white"
                }`}
                title={doc.filename}
              >
                {doc.source_type === "public_corpus" ? "🌐 " : ""}
                {doc.filename}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="border-t border-navy/10 p-4">
        <button onClick={onLogout} className="text-xs text-navy/40 hover:text-navy">
          Log out
        </button>
      </div>
    </aside>
  );
}
