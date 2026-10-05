"use client";

import { useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentOut } from "@/lib/api";

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
    <aside className="flex h-full w-72 flex-col border-r border-slate-200 bg-slate-50">
      <div className="border-b border-slate-200 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-400">Workspace</p>
        <p className="truncate text-sm font-semibold text-slate-900">{workspaceName}</p>
      </div>

      <div className="border-b border-slate-200 p-4">
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
          className="block w-full cursor-pointer rounded-md border border-dashed border-slate-300 bg-white px-3 py-2 text-center text-sm text-slate-600 hover:bg-slate-100"
        >
          {uploading ? "Uploading..." : "+ Upload PDF / DOCX"}
        </label>
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <p className="px-2 pb-1 pt-2 text-xs uppercase tracking-wide text-slate-400">Documents</p>
        {documents.length === 0 && (
          <p className="px-2 py-4 text-sm text-slate-400">No documents yet. Upload one to get started.</p>
        )}
        <ul className="space-y-1">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                onClick={() => onSelectDocument(doc.id)}
                className={`block w-full truncate rounded-md px-2 py-2 text-left text-sm ${
                  selectedDocumentId === doc.id ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
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

      <div className="border-t border-slate-200 p-4">
        <button onClick={onLogout} className="text-xs text-slate-400 hover:text-slate-600">
          Log out
        </button>
      </div>
    </aside>
  );
}
