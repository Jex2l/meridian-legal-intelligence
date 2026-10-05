"use client";

import { useCallback, useEffect, useState } from "react";
import AuthForm from "@/components/AuthForm";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";
import SourceViewer from "@/components/SourceViewer";
import { api } from "@/lib/api";
import type { AuthSession, Citation, DocumentOut } from "@/lib/api";
import { clearSession, loadSession, saveSession } from "@/lib/session";

export default function Home() {
  const [session, setSession] = useState<AuthSession | null | undefined>(undefined);
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [highlightChunkId, setHighlightChunkId] = useState<string | null>(null);

  useEffect(() => {
    setSession(loadSession());
  }, []);

  const refreshDocuments = useCallback((token: string) => {
    api.listDocuments(token).then(setDocuments).catch(() => setDocuments([]));
  }, []);

  useEffect(() => {
    if (session) refreshDocuments(session.access_token);
  }, [session, refreshDocuments]);

  function handleAuthenticated(s: AuthSession) {
    saveSession(s);
    setSession(s);
  }

  function handleLogout() {
    clearSession();
    setSession(null);
    setDocuments([]);
    setSelectedDocumentId(null);
  }

  function handleCitationClick(citation: Citation) {
    setSelectedDocumentId(citation.document_id);
    setHighlightChunkId(citation.chunk_id);
  }

  if (session === undefined) {
    return null; // avoid a login-form flash before localStorage is read
  }

  if (!session) {
    return <AuthForm onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div className="flex h-screen">
      <Sidebar
        token={session.access_token}
        documents={documents}
        selectedDocumentId={selectedDocumentId}
        onSelectDocument={(id) => {
          setSelectedDocumentId(id);
          setHighlightChunkId(null);
        }}
        onUploaded={() => refreshDocuments(session.access_token)}
        workspaceName={session.name}
        onLogout={handleLogout}
      />
      <main className="flex min-w-0 flex-1">
        <div className="w-1/2 border-r border-navy/10">
          <Chat token={session.access_token} onCitationClick={handleCitationClick} />
        </div>
        <div className="w-1/2">
          <SourceViewer token={session.access_token} documentId={selectedDocumentId} highlightChunkId={highlightChunkId} />
        </div>
      </main>
    </div>
  );
}
